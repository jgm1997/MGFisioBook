from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    admin,
    appointment,
    auth,
    availability,
    free_slots,
    invoice,
    patient,
    therapist,
    treatment,
)

app = FastAPI(title="MGFisioBook API", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mgfisiobook.onrender.com", "http://localhost", "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(patient.router, prefix="/patients", tags=["patients"])
app.include_router(therapist.router, prefix="/therapists", tags=["therapists"])
app.include_router(appointment.router, prefix="/appointments", tags=["appointments"])
app.include_router(availability.router, prefix="/availability", tags=["availability"])
app.include_router(invoice.router, prefix="/invoices", tags=["invoices"])
app.include_router(treatment.router, prefix="/treatments", tags=["treatments"])
app.include_router(free_slots.router, prefix="/free-slots", tags=["free slots"])


@app.get("/")
async def root_redirect():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/docs")
