from app.schemas.field_definition import (
    FieldDefinition,
    FieldOption,
    ProfileFieldCatalogItem,
)


DEFAULT_PROFILE_FIELDS = [
    ProfileFieldCatalogItem(
        field_definition=FieldDefinition(
            key="residence",
            label="거주 지역",
            data_type="string",
            question="현재 거주하는 강남구의 동을 알려주세요.",
            sensitivity="medium",
            validity_days=365,
            review_status="approved",
        ),
        onboarding_group="core",
        eligibility_usable=True,
        display_order=10,
    ),
    ProfileFieldCatalogItem(
        field_definition=FieldDefinition(
            key="age",
            label="연령",
            data_type="number",
            question="현재 만 나이를 입력해 주세요.",
            sensitivity="low",
            validity_days=365,
            review_status="approved",
        ),
        onboarding_group="core",
        eligibility_usable=True,
        display_order=20,
    ),
    ProfileFieldCatalogItem(
        field_definition=FieldDefinition(
            key="employment_status",
            label="현재 취업 상태",
            data_type="enum",
            allowed_values=[
                FieldOption(value="employed", label="현재 취업 중이에요"),
                FieldOption(value="unemployed", label="현재 미취업 상태예요"),
                FieldOption(value="self_employed", label="자영업·프리랜서예요"),
                FieldOption(value="student", label="학생이에요"),
                FieldOption(value="none_of_above", label="해당 사항 없음"),
            ],
            question="현재 본인의 취업 상태를 선택해 주세요.",
            sensitivity="medium",
            validity_days=90,
            review_status="approved",
        ),
        onboarding_group="core",
        eligibility_usable=True,
        display_order=30,
    ),
    ProfileFieldCatalogItem(
        field_definition=FieldDefinition(
            key="frequent_bus_stops",
            label="자주 이용하는 정류장",
            data_type="list",
            question="강남구에서 자주 이용하는 정류장 이름을 알려주세요.",
            sensitivity="low",
            validity_days=180,
            review_status="approved",
        ),
        onboarding_group="core",
        eligibility_usable=False,
        display_order=40,
    ),
    ProfileFieldCatalogItem(
        field_definition=FieldDefinition(
            key="interest_categories",
            label="관심 분야",
            data_type="list",
            allowed_values=[
                FieldOption(value="youth_jobs", label="청년 · 일자리"),
                FieldOption(value="housing_living", label="주거 · 생활 지원"),
                FieldOption(value="welfare_care", label="복지 · 돌봄"),
                FieldOption(value="culture_sports", label="문화 · 체육"),
                FieldOption(value="transport_facilities", label="교통 · 시설"),
                FieldOption(value="education_family", label="교육 · 가족"),
            ],
            question="관심 있는 분야를 선택해 주세요.",
            sensitivity="low",
            validity_days=None,
            review_status="approved",
        ),
        onboarding_group="optional",
        eligibility_usable=False,
        display_order=50,
    ),
]
