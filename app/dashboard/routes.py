from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_dashboard_user, get_current_user_from_cookie_or_header
from app.models.organization import Organization, PlanType, SubscriptionStatus
from app.models.user import User, UserRole
from app.models.invitation import Invitation
from app.services.billing.factory import get_billing_service
from app.core.config import settings

# Create dashboard templates directory locator
templates = Jinja2Templates(directory="app/dashboard/templates")

router = APIRouter(tags=["Dashboard UI"])


@router.get("/", response_class=HTMLResponse)
async def root_page(request: Request, user: User | None = Depends(get_current_user_from_cookie_or_header)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: User | None = Depends(get_current_user_from_cookie_or_header)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("dashboard/login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    from app.core.auth import get_user_manager
    from app.core.security.jwt import create_access_token
    from fastapi.security import OAuth2PasswordRequestForm
    from app.core.config import settings
    
    # Authenticate credentials manually using user manager
    try:
        from types import SimpleNamespace
        credentials = SimpleNamespace(username=email, password=password)
        
        # Resolve manager
        from app.core.auth import SQLAlchemyUserDatabase
        user_db = SQLAlchemyUserDatabase(db, User)
        from app.core.auth import UserManager
        manager = UserManager(user_db)
        
        user = await manager.authenticate(credentials)
        
        if not user or not user.is_active:
            return templates.TemplateResponse(
                "dashboard/login.html",
                {"request": request, "error": "Invalid email or password"}
            )
            
        # Create access token and set in cookie
        token = create_access_token(str(user.id))
        
        redirect_res = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        # Store in cookie (expires in 1 day for convenience)
        redirect_res.set_cookie(
            key="fastapiusersauth",
            value=token,
            httponly=True,
            samesite="lax",
            secure=settings.ENVIRONMENT == "production"
        )
        return redirect_res
    except Exception as e:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse(
            "dashboard/login.html",
            {"request": request, "error": "Invalid email or password"}
        )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: User | None = Depends(get_current_user_from_cookie_or_header)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("dashboard/register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Register user
    try:
        from app.core.auth import SQLAlchemyUserDatabase, UserManager
        user_db = SQLAlchemyUserDatabase(db, User)
        manager = UserManager(user_db)
        
        from fastapi_users import schemas
        class UserCreateMock(schemas.BaseUserCreate):
            email: str = email
            password: str = password
            
        user_create = UserCreateMock()
        # Create user via manager
        user = await manager.create(user_create, request=request)
        
        return RedirectResponse(url="/login?registered=true", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            "dashboard/register.html",
            {"request": request, "error": f"Registration failed: {str(e)}"}
        )


@router.get("/logout")
async def logout(response: Response):
    redirect_res = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect_res.delete_cookie("fastapiusersauth")
    return redirect_res


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_home(
    request: Request,
    user: User = Depends(require_dashboard_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.org_id:
        return RedirectResponse(url="/dashboard/setup-org")
        
    stmt = select(Organization).where(Organization.id == user.org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    
    return templates.TemplateResponse(
        "dashboard/index.html",
        {"request": request, "user": user, "org": org}
    )


@router.get("/dashboard/setup-org", response_class=HTMLResponse)
async def setup_org_page(request: Request, user: User = Depends(require_dashboard_user)):
    if user.org_id:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("dashboard/setup_org.html", {"request": request, "user": user, "error": None})


@router.post("/dashboard/setup-org", response_class=HTMLResponse)
async def setup_org_post(
    request: Request,
    org_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dashboard_user)
):
    if user.org_id:
        return RedirectResponse(url="/dashboard")
        
    try:
        slug_base = org_name.lower().replace(" ", "-")
        org = Organization(
            name=org_name,
            slug=f"{slug_base}-{uuid4().hex[:6]}",
            plan=PlanType.FREE,
            subscription_status=SubscriptionStatus.TRIALING,
            trial_ends_at=datetime.now(timezone.utc),
            is_active=True
        )
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        # Set user as Admin of org
        user.org_id = org.id
        user.role = UserRole.ADMIN
        db.add(user)
        await db.commit()
        
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            "dashboard/setup_org.html",
            {"request": request, "user": user, "error": f"Failed to create workspace: {str(e)}"}
        )


@router.get("/dashboard/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: User = Depends(require_dashboard_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).where(Organization.id == user.org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    
    return templates.TemplateResponse(
        "dashboard/profile.html",
        {"request": request, "user": user, "org": org, "success": None, "error": None}
    )


@router.post("/dashboard/profile", response_class=HTMLResponse)
async def profile_post(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dashboard_user)
):
    stmt = select(Organization).where(Organization.id == user.org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    
    try:
        user.email = email
        db.add(user)
        await db.commit()
        return templates.TemplateResponse(
            "dashboard/profile.html",
            {"request": request, "user": user, "org": org, "success": "Profile updated successfully!", "error": None}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "dashboard/profile.html",
            {"request": request, "user": user, "org": org, "success": None, "error": f"Update failed: {str(e)}"}
        )


@router.get("/dashboard/team", response_class=HTMLResponse)
async def team_page(
    request: Request,
    user: User = Depends(require_dashboard_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch team members
    stmt_members = select(User).where(User.org_id == user.org_id)
    res_members = await db.execute(stmt_members)
    members = res_members.scalars().all()
    
    # Fetch active invitations
    stmt_invites = select(Invitation).where(Invitation.org_id == user.org_id)
    res_invites = await db.execute(stmt_invites)
    invitations = res_invites.scalars().all()
    
    stmt_org = select(Organization).where(Organization.id == user.org_id)
    res_org = await db.execute(stmt_org)
    org = res_org.scalar_one_or_none()
    
    return templates.TemplateResponse(
        "dashboard/team.html",
        {
            "request": request,
            "user": user,
            "org": org,
            "members": members,
            "invitations": invitations,
            "error": None,
            "success": None
        }
    )


@router.post("/dashboard/team/invite", response_class=HTMLResponse)
async def invite_member(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dashboard_user)
):
    # Reload members/invites data
    stmt_members = select(User).where(User.org_id == user.org_id)
    res_members = await db.execute(stmt_members)
    members = res_members.scalars().all()
    
    stmt_org = select(Organization).where(Organization.id == user.org_id)
    res_org = await db.execute(stmt_org)
    org = res_org.scalar_one_or_none()
    
    try:
        from app.services.invitation_service import invitation_service
        # Use invitation service
        await invitation_service.create_invitation(
            db=db,
            org_id=user.org_id,
            email=email,
            role=UserRole.USER,
            invited_by_id=user.id
        )
        
        stmt_invites = select(Invitation).where(Invitation.org_id == user.org_id)
        res_invites = await db.execute(stmt_invites)
        invitations = res_invites.scalars().all()
        
        return templates.TemplateResponse(
            "dashboard/team.html",
            {
                "request": request,
                "user": user,
                "org": org,
                "members": members,
                "invitations": invitations,
                "success": f"Invitation sent to {email} successfully!",
                "error": None
            }
        )
    except Exception as e:
        stmt_invites = select(Invitation).where(Invitation.org_id == user.org_id)
        res_invites = await db.execute(stmt_invites)
        invitations = res_invites.scalars().all()
        
        return templates.TemplateResponse(
            "dashboard/team.html",
            {
                "request": request,
                "user": user,
                "org": org,
                "members": members,
                "invitations": invitations,
                "success": None,
                "error": f"Failed to invite member: {str(e)}"
            }
        )


@router.get("/dashboard/billing", response_class=HTMLResponse)
async def billing_page(
    request: Request,
    user: User = Depends(require_dashboard_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Organization).where(Organization.id == user.org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    
    # Active Billing Config
    billing_provider = settings.BILLING_PROVIDER
    
    return templates.TemplateResponse(
        "dashboard/billing.html",
        {
            "request": request,
            "user": user,
            "org": org,
            "billing_provider": billing_provider,
            "success": None
        }
    )


@router.post("/dashboard/billing/subscribe", response_class=HTMLResponse)
async def subscribe_post(
    request: Request,
    plan: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_dashboard_user)
):
    stmt = select(Organization).where(Organization.id == user.org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    
    try:
        billing_service = get_billing_service()
        checkout_url = await billing_service.create_checkout_session(
            org_id=user.org_id,
            plan=PlanType(plan),
            email=user.email
        )
        return RedirectResponse(url=checkout_url, status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        return templates.TemplateResponse(
            "dashboard/billing.html",
            {
                "request": request,
                "user": user,
                "org": org,
                "billing_provider": settings.BILLING_PROVIDER,
                "error": f"Checkout session creation failed: {str(e)}"
            }
        )


@router.get("/dashboard/billing/payoneer", response_class=HTMLResponse)
async def payoneer_checkout_mock(
    request: Request,
    org_id: UUID,
    plan: str,
    email: str
):
    """Mocks the Payoneer Hosted Checkout page for simulation."""
    return templates.TemplateResponse(
        "dashboard/payoneer_checkout.html",
        {
            "request": request,
            "org_id": org_id,
            "plan": plan,
            "email": email
        }
    )


@router.post("/dashboard/billing/payoneer/complete", response_class=HTMLResponse)
async def payoneer_checkout_complete(
    request: Request,
    org_id: UUID = Form(...),
    plan: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Callback simulation that marks Payoneer checkout as paid."""
    # Simulate callback locally
    stmt = select(Organization).where(Organization.id == org_id)
    res = await db.execute(stmt)
    org = res.scalar_one_or_none()
    
    if org:
        org.billing_provider = "payoneer"
        org.billing_customer_id = f"payoneer_cust_{uuid4().hex[:6]}"
        org.billing_subscription_id = f"payoneer_sub_{uuid4().hex[:8]}"
        org.subscription_status = SubscriptionStatus.ACTIVE
        org.plan = PlanType(plan)
        db.add(org)
        await db.commit()
        
    return RedirectResponse(url="/dashboard/billing?status=success", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/docs/{slug}", response_class=HTMLResponse)
async def view_doc(request: Request, slug: str):
    from app.services.markdown_service import markdown_service
    doc = markdown_service.get_content("docs", slug)
    if not doc:
        raise HTTPException(status_code=404, detail="Documentation page not found")
    docs_list = markdown_service.list_posts("docs")
    return templates.TemplateResponse(
        "docs/detail.html",
        {
            "request": request,
            "doc": doc,
            "docs_list": docs_list
        }
    )


@router.get("/blog", response_class=HTMLResponse)
async def list_blog_posts(request: Request):
    from app.services.markdown_service import markdown_service
    posts = markdown_service.list_posts("blog")
    return templates.TemplateResponse(
        "blog/index.html",
        {
            "request": request,
            "posts": posts
        }
    )


@router.get("/blog/{slug}", response_class=HTMLResponse)
async def view_blog_post(request: Request, slug: str):
    from app.services.markdown_service import markdown_service
    post = markdown_service.get_content("blog", slug)
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return templates.TemplateResponse(
        "blog/detail.html",
        {
            "request": request,
            "post": post
        }
    )

