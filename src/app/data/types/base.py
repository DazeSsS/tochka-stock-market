from datetime import datetime
from typing import Annotated
from sqlalchemy import func, DateTime
from sqlalchemy.orm import mapped_column


ID = Annotated[int, mapped_column(primary_key=True)]

CreatedAt = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]
