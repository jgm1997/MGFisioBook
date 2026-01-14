from fastapi.templating import Jinja2Templates

from app.core.email import send_email
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.therapist import Therapist
from app.models.treatment import Treatment

templates = Jinja2Templates(directory="app/templates")


async def send_appointment(
    type: str,
    patient: Patient,
    therapist: Therapist,
    treatment: Treatment,
    appointment: Appointment,
):
    date_str = appointment.start_time.strftime("%d/%m/%Y")
    time_str = appointment.start_time.strftime("%H:%M")

    html = templates.TemplateResponse(
        f"email/appointment_{type}.html",
        {
            "therapist": therapist,
            "treatment": treatment,
            "date": date_str,
            "time": time_str,
        },
    )
    await send_email(
        to=patient.email,
        subject=f"Appointment {type.capitalize()}",
        html=html.body.decode(),
    )
