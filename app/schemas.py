from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    role: str = "user"


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PositionCreate(BaseModel):
    title: str
    amount: float
    comment: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = 0


class PositionUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = None
    comment: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = None


class PositionResponse(BaseModel):
    id: int
    version_id: int
    title: str
    amount: float
    amount_formatted: Optional[str] = None
    comment: Optional[str] = None
    category: Optional[str] = None
    sort_order: int


class ContributionCreate(BaseModel):
    person_name: str
    amount: float
    comment: Optional[str] = None
    sort_order: Optional[int] = 0


class ContributionUpdate(BaseModel):
    person_name: Optional[str] = None
    amount: Optional[float] = None
    comment: Optional[str] = None
    sort_order: Optional[int] = None


class ContributionResponse(BaseModel):
    id: int
    version_id: int
    person_name: str
    amount: float
    amount_formatted: Optional[str] = None
    comment: Optional[str] = None
    sort_order: int


class VersionCreate(BaseModel):
    title: str
    effective_date: Optional[str] = None
    copy_from_version_id: Optional[int] = None


class VersionUpdate(BaseModel):
    title: Optional[str] = None
    effective_date: Optional[str] = None



class VersionResponse(BaseModel):
    id: int
    plan_id: int
    title: str
    effective_date: Optional[str] = None
    is_active: int
    created_at: Optional[str] = None
    positions: List[PositionResponse] = []
    contributions: List[ContributionResponse] = []
    totals: Dict[str, Any] = {}


class VersionSaveRequest(BaseModel):
    title: str
    effective_date: Optional[str] = None
    positions: List[PositionCreate] = []
    contributions: List[ContributionCreate] = []


class HistoryVersionSummary(BaseModel):
    id: int
    plan_id: int
    title: str
    effective_date: Optional[str] = None
    is_active: int
    created_at: Optional[str] = None
    positions_count: int
    contributions_count: int
    totals: Dict[str, Any] = {}


class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class PlanResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    active_version: Optional[VersionResponse] = None
    versions: List[Dict[str, Any]] = []


class HistoryRow(BaseModel):
    title: str
    category: Optional[str] = None
    comment: Optional[str] = None
    values: Dict[str, Optional[float]] = {}
    formatted_values: Dict[str, Optional[str]] = {}


class HistoryComparisonResponse(BaseModel):
    versions: List[Dict[str, Any]]
    rows: List[HistoryRow]
    contributions_rows: List[HistoryRow]
    totals: Dict[str, Dict[str, Any]]


# --- Export / Import Schemas ---

class ExportPositionData(BaseModel):
    title: str
    amount: float
    comment: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = 0


class ExportContributionData(BaseModel):
    person_name: str
    amount: float
    comment: Optional[str] = None
    sort_order: Optional[int] = 0


class ExportVersionData(BaseModel):
    title: str
    effective_date: Optional[str] = None
    is_active: Optional[int] = 1
    positions: List[ExportPositionData] = []
    contributions: List[ExportContributionData] = []


class ExportPlanData(BaseModel):
    title: str
    description: Optional[str] = None
    versions: List[ExportVersionData] = []


class FullExportData(BaseModel):
    version: int = 1
    exported_at: Optional[str] = None
    plans: List[ExportPlanData] = []

