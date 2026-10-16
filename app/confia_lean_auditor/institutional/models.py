"""Closed contracts for the state network hierarchy and its memberships."""
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

InstitutionId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9._-]{0,79}$")]
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class InstitutionalModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Network(InstitutionalModel):
    network_id: InstitutionId
    name: DisplayName
    active: bool = True


class School(InstitutionalModel):
    school_id: InstitutionId
    network_id: InstitutionId
    name: DisplayName
    code: InstitutionId
    municipality: DisplayName
    active: bool = True


class Classroom(InstitutionalModel):
    classroom_id: InstitutionId
    school_id: InstitutionId
    name: DisplayName
    grade: DisplayName
    shift: DisplayName
    academic_year: int = Field(ge=2000, le=2100)
    active: bool = True


class TeacherAssignment(InstitutionalModel):
    teacher_user_id: str = Field(min_length=1, max_length=80)
    school_id: InstitutionId
    classroom_id: InstitutionId
    academic_year: int = Field(ge=2000, le=2100)
    active: bool = True


class Enrollment(InstitutionalModel):
    student_user_id: str = Field(min_length=1, max_length=80)
    school_id: InstitutionId
    classroom_id: InstitutionId
    academic_year: int = Field(ge=2000, le=2100)
    active: bool = True


class ManagerAssignment(InstitutionalModel):
    manager_user_id: str = Field(min_length=1, max_length=80)
    network_id: Optional[InstitutionId] = None
    school_id: Optional[InstitutionId] = None
    active: bool = True

    @model_validator(mode="after")
    def one_scope(self):
        if (self.network_id is None) == (self.school_id is None):
            raise ValueError("manager assignment requires exactly one scope")
        return self


class InstitutionalData(InstitutionalModel):
    networks: list[Network] = Field(default_factory=list)
    schools: list[School] = Field(default_factory=list)
    classrooms: list[Classroom] = Field(default_factory=list)
    teacher_assignments: list[TeacherAssignment] = Field(default_factory=list)
    enrollments: list[Enrollment] = Field(default_factory=list)
    manager_assignments: list[ManagerAssignment] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_hierarchy(self):
        for name, key in (("networks", "network_id"), ("schools", "school_id"),
                          ("classrooms", "classroom_id")):
            values = [getattr(item, key) for item in getattr(self, name)]
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {name} ID")
        networks = {item.network_id for item in self.networks}
        schools = {item.school_id: item for item in self.schools}
        classrooms = {item.classroom_id: item for item in self.classrooms}
        if any(item.network_id not in networks for item in self.schools):
            raise ValueError("school has no network")
        if any(item.school_id not in schools for item in self.classrooms):
            raise ValueError("classroom has no school")
        for item in [*self.teacher_assignments, *self.enrollments]:
            classroom = classrooms.get(item.classroom_id)
            if classroom is None or classroom.school_id != item.school_id or classroom.academic_year != item.academic_year:
                raise ValueError("membership classroom mismatch")
        for item in self.manager_assignments:
            if item.school_id is not None and item.school_id not in schools:
                raise ValueError("manager school missing")
            if item.network_id is not None and item.network_id not in networks:
                raise ValueError("manager network missing")
        return self


class InstitutionalContext(InstitutionalModel):
    role: Literal["STUDENT", "TEACHER", "SCHOOL_MANAGER", "NETWORK_MANAGER", "ADMIN"]
    academic_year: int
    schools: list[School]
    classrooms: list[Classroom]
    selected_school_id: Optional[InstitutionId] = None
    selected_classroom_id: Optional[InstitutionId] = None
