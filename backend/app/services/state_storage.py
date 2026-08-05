from copy import deepcopy

from app.database import SessionLocal
from app.models import AppState


StateValue = dict[str, object] | list[dict[str, object]]


def load_state(key: str, default: StateValue) -> StateValue:
    with SessionLocal.begin() as session:
        record = session.get(AppState, key)
        if record is None:
            record = AppState(key=key, value=deepcopy(default))
            session.add(record)
        return deepcopy(record.value)


# ponytail: whole-document writes suit the MVP; normalize rows if concurrent edits matter.
def save_state(key: str, value: StateValue) -> None:
    with SessionLocal.begin() as session:
        record = session.get(AppState, key)
        if record is None:
            session.add(AppState(key=key, value=deepcopy(value)))
        else:
            record.value = deepcopy(value)
