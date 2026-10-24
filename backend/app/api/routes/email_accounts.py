
import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.email_account import EmailAccount
from app.models.organization import Organization
from app.schemas.email_account import EmailAccountCreate, EmailAccountRead

router = APIRouter(prefix="/email-accounts", tags=["Email Accounts"])

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
STATE_COOKIE = "inboxops_google_oauth_state"
PKCE_COOKIE = "inboxops_google_pkce"
STATE_TTL_SECONDS = 600
GOOGLE_OAUTH_PATH = "/api/v1/email-accounts/google"


def _require_google_config() -> None:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured.",
        )
    if not settings.token_encryption_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token encryption is not configured.",
        )


def _fernet() -> Fernet:
    _require_google_config()
    try:
        return Fernet(settings.token_encryption_key.encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token encryption configuration is invalid.",
        ) from exc


def _encode_state_payload(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_state_payload(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _create_state(organization_id: int) -> str:
    payload = json.dumps(
        {
            "organization_id": organization_id,
            "issued_at": int(time.time()),
            "nonce": secrets.token_urlsafe(24),
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    encoded_payload = _encode_state_payload(payload)
    signature = hmac.new(
        settings.token_encryption_key.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()

    return f"{encoded_payload}.{_encode_state_payload(signature)}"


def _validate_state(state: str, cookie_state: str | None) -> dict:
    if not cookie_state or not hmac.compare_digest(state, cookie_state):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state validation failed. Please try connecting again.",
        )

    try:
        encoded_payload, encoded_signature = state.split(".", 1)
        supplied_signature = _decode_state_payload(encoded_signature)
        expected_signature = hmac.new(
            settings.token_encryption_key.encode("utf-8"),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()

        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("Invalid signature")

        payload = json.loads(_decode_state_payload(encoded_payload))
        issued_at = int(payload["issued_at"])

        if (
            not payload.get("nonce")
            or issued_at > int(time.time()) + 60
            or time.time() - issued_at > STATE_TTL_SECONDS
        ):
            raise ValueError("Expired or invalid state")

        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state is invalid or expired. Please try again.",
        ) from exc


def _google_flow(state: str | None = None) -> Flow:
    _require_google_config()

    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=GOOGLE_SCOPES,
        state=state,
    )
    flow.redirect_uri = settings.google_redirect_uri
    return flow


@router.post(
    "",
    response_model=EmailAccountRead,
    status_code=status.HTTP_201_CREATED,
)
def create_email_account(
    payload: EmailAccountCreate,
    db: Session = Depends(get_db),
):
    organization = db.get(Organization, payload.organization_id)

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    email_account = EmailAccount(
        organization_id=payload.organization_id,
        provider=payload.provider.strip().lower(),
        email_address=str(payload.email_address).lower(),
        display_name=payload.display_name,
    )
    db.add(email_account)

    try:
        db.commit()
        db.refresh(email_account)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This email account is already registered for this "
                "organization and provider."
            ),
        )

    return email_account


@router.get("", response_model=list[EmailAccountRead])
def list_email_accounts(
    organization_id: int,
    db: Session = Depends(get_db),
):
    statement = (
        select(EmailAccount)
        .where(EmailAccount.organization_id == organization_id)
        .order_by(EmailAccount.id)
    )
    return db.scalars(statement).all()


@router.get("/{email_account_id}", response_model=EmailAccountRead)
def get_email_account(
    email_account_id: int,
    db: Session = Depends(get_db),
):
    email_account = db.get(EmailAccount, email_account_id)

    if email_account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found.",
        )

    return email_account


@router.get("/google/connect", include_in_schema=True)
def connect_google(
    organization_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    _require_google_config()

    if db.get(Organization, organization_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    state = _create_state(organization_id)
    flow = _google_flow(state=state)

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    response = RedirectResponse(authorization_url, status_code=302)
    response.set_cookie(
        key=STATE_COOKIE,
        value=state,
        max_age=STATE_TTL_SECONDS,
        httponly=True,
        secure=False,
        samesite="lax",
        path=GOOGLE_OAUTH_PATH,
    )

    if flow.code_verifier:
        response.set_cookie(
            key=PKCE_COOKIE,
            value=flow.code_verifier,
            max_age=STATE_TTL_SECONDS,
            httponly=True,
            secure=False,  # Local HTTP development only.
            samesite="lax",
            path=GOOGLE_OAUTH_PATH,
        )
    return response


@router.get("/google/callback", include_in_schema=True)
def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    _require_google_config()

    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return OAuth state. Please try again.",
        )

    state_payload = _validate_state(
        state,
        request.cookies.get(STATE_COOKIE),
    )

    if error:
        response = JSONResponse(
            {"detail": "Google authorization was not completed."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        response.delete_cookie(STATE_COOKIE, path=GOOGLE_OAUTH_PATH)
        return response

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return an authorization code.",
        )
        
    try:
        pkce_verifier = request.cookies.get(PKCE_COOKIE)

        if not pkce_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "OAuth verification cookie is missing. "
                    "Please reconnect Gmail."
                ),
            )

        flow = _google_flow(state=state)
        flow.code_verifier = pkce_verifier
        flow.fetch_token(code=code)

        gmail = build(
            "gmail",
            "v1",
            credentials=flow.credentials,
            cache_discovery=False,
        )
        profile = gmail.users().getProfile(userId="me").execute()
        email_address = profile["emailAddress"].strip().lower()

        encrypted_credentials = _fernet().encrypt(
            flow.credentials.to_json().encode("utf-8")
        ).decode("ascii")

    except HTTPException:
        raise
    except Exception as exc:
        # Do not expose OAuth responses, tokens, or provider error details.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Could not complete Google authorization. "
                "Check the OAuth configuration and try again."
            ),
        ) from exc


    response = JSONResponse(
        {
            "message": "Gmail connected successfully.",
            "email_account_id": email_account.id,
            "organization_id": organization_id,
            "email_address": email_account.email_address,
            "status": email_account.status,
            "scope": GOOGLE_SCOPES,
        }
    )
    response.delete_cookie(STATE_COOKIE, path=GOOGLE_OAUTH_PATH)
    response.delete_cookie(PKCE_COOKIE, path=GOOGLE_OAUTH_PATH)
    return response
