# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from api.routers import users, assessment, lesson, practice

app = FastAPI(title="VocAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # prod'da frontend URL ile kısıtlanacak
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(assessment.router, prefix="/v1/assessment", tags=["assessment"])
app.include_router(lesson.router, prefix="/v1/lesson", tags=["lesson"])
app.include_router(practice.router, prefix="/v1/practice", tags=["practice"])


@app.get("/")
def root():
    return {"status": "ok", "version": "1.0.0"}
