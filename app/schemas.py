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
    can_manage_plans: bool = False
    can_export: bool = True
    can_import: bool = False
    can_manage_backups: bool = False
    can_manage_users: bool = False
    can_run_testsuite: bool = False
    can_view_changelog: bool = True
    assigned_plan_ids: Optional[List[int]] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    can_manage_plans: Optional[bool] = None
    can_export: Optional[bool] = None
    can_import: Optional[bool] = None
    can_manage_backups: Optional[bool] = None
    can_manage_users: Optional[bool] = None
    can_run_testsuite: Optional[bool] = None
    can_view_changelog: Optional[bool] = None
    assigned_plan_ids: Optional[List[int]] = None


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    can_manage_plans: bool = False
    can_export: bool = True
    can_import: bool = False
    can_manage_backups: bool = False
    can_manage_users: bool = False
    can_run_testsuite: bool = False
    can_view_changelog: bool = True
    assigned_plan_ids: List[int] = []

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
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
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
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
    positions_count: int
    contributions_count: int
    totals: Dict[str, Any] = {}


class PlanCreate(BaseModel):
    title: str
    description: Optional[str] = None


class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_archived: Optional[bool] = None


class PlanDuplicateRequest(BaseModel):
    title: Optional[str] = None


class PlanResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_archived: bool = False
    created_at: Optional[str] = None
    active_version: Optional[VersionResponse] = None
    versions: List[Dict[str, Any]] = []


class PlanSummaryResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    is_archived: bool = False
    created_at: Optional[str] = None
    versions_count: int = 0
    active_version_id: Optional[int] = None
    active_version_title: Optional[str] = None
    total_expenses: Optional[float] = None
    total_contributions: Optional[float] = None
    total_balance: Optional[float] = None


class AppInfoResponse(BaseModel):
    app_name: str
    version: str
    environment: str
    status: str


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
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
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


# --- Backup Engine Schemas ---
class BackupSettingsResponse(BaseModel):
    id: int = 1
    backup_enabled: bool = True
    backup_frequency: str = "daily"
    backup_folder: str = "data/backups"
    retention_count: int = 14
    auto_backup_time: str = "03:00"
    last_backup_at: Optional[str] = None


class BackupSettingsUpdate(BaseModel):
    backup_enabled: Optional[bool] = None
    backup_frequency: Optional[str] = None
    backup_folder: Optional[str] = None
    retention_count: Optional[int] = None
    auto_backup_time: Optional[str] = None


class BackupFileInfo(BaseModel):
    filename: str
    file_size: int
    file_size_formatted: str
    created_at: str


class BackupCreateResponse(BaseModel):
    filename: str
    path: str
    file_size: int
    file_size_formatted: str
    created_at: str
    pruned_files: List[str] = []
    total_backups_count: int = 1


