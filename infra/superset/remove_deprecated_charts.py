from superset.app import create_app

DEPRECATED_SLICE_NAMES = {
    "ABC: Доля клиентов по месяцам (%)",
    "ABC: Матрица миграции категорий",
}


def remove_deprecated_charts() -> int:
    app = create_app()
    with app.app_context():
        from superset.extensions import db
        from superset.models.slice import Slice

        deprecated_slices = (
            db.session.query(Slice)
            .filter(Slice.slice_name.in_(sorted(DEPRECATED_SLICE_NAMES)))
            .all()
        )
        removed = len(deprecated_slices)
        for slice_ in deprecated_slices:
            db.session.delete(slice_)
        db.session.commit()
        return removed


if __name__ == "__main__":
    removed = remove_deprecated_charts()
    print(f"Removed {removed} deprecated charts.")
