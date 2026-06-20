from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.database import get_db
from app.models.job import Job, Application, ApplicationStatus
from app.models.user import User
from app.schemas.job import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.auth_utils import get_current_user

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse, status_code=201)
def create_application(
    app_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check job exists
    job = db.query(Job).filter(Job.id == app_data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check not already applied
    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == app_data.job_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")

    new_application = Application(
        user_id=current_user.id,
        job_id=app_data.job_id,
        notes=app_data.notes
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    # Reload with job details for nested response
    return db.query(Application).options(
        joinedload(Application.job)
    ).filter(Application.id == new_application.id).first()


@router.get("/", response_model=List[ApplicationResponse])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Application).options(
        joinedload(Application.job)
    ).filter(Application.user_id == current_user.id).all()


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = db.query(Application).options(
        joinedload(Application.job)
    ).filter(
        Application.id == application_id,
        Application.user_id == current_user.id  # users can only see their own
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application_status(
    application_id: int,
    update_data: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    changes = update_data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    return db.query(Application).options(
        joinedload(Application.job)
    ).filter(Application.id == application_id).first()


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(application)
    db.commit()