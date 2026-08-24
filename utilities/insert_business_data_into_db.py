import json

from tqdm import tqdm

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.models.business import Business
from app.models.category import Category

JSON_FILE = "D:/Sculptsoft/business-mention-resolution/data/raw_data/yelp_academic_dataset_business.json"

BATCH_SIZE = 1000

def import_businesses(session: Session):

    try:
        # Cache categories already present in database
        category_cache = {}

        existing_categories = session.execute(select(Category)).scalars().all()

        for category in existing_categories:
            category_cache[category.name] = category

        count = 0

        with open(JSON_FILE, 'r', encoding='utf-8') as file:

            for line in tqdm(file, desc="Importing businesses", unit="business"):

                data = json.loads(line)

                # ------------------------------------------------
                # 1. Avoid inserting duplicate businesses
                # ------------------------------------------------

                existing_business = session.execute(
                    select(Business).where(
                        Business.business_id == data['business_id']
                    )
                ).scalar_one_or_none()

                if existing_business:
                    continue

                # ------------------------------------------------
                # 2. Create Business
                # ------------------------------------------------

                business = Business(
                    business_id=data['business_id'],
                    name=data['name'],
                    address=data.get('address'),
                    city=data.get('city'),
                    state=data.get('state'),
                    postal_code=data.get('postal_code'),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude'),

                    is_verified=True
                )

                # ------------------------------------------------
                # 3. Process categories
                # ------------------------------------------------

                categories = data.get("categories")

                if categories:

                    category_names = [
                        category.strip()
                        for category in categories.split(",")
                        if category.strip()
                    ]

                    for category_name in category_names:
                        if category_name in category_cache:
                            category = category_cache[category_name]

                        else:
                            category = Category(
                                name=category_name
                            )

                            session.add(category)

                            # Put it in cache so we don't
                            # query/create it repeatedly
                            category_cache[category_name] = category

                        # Connect Business <--> Category
                        business.categories.append(category)

                # ------------------------------------------------
                # 4. Add Business
                # ------------------------------------------------

                session.add(business)

                count += 1

                # ------------------------------------------------
                # 5. Commit in batches
                # ------------------------------------------------

                if count % BATCH_SIZE == 0:

                    session.commit()

                    print(
                        f"Imported {count} businesses..."
                    )

        # Commit remaining records
        session.commit()

        print(
            f"Import completed successfully. "
            f"Total businesses imported: {count}"
        )


    except Exception as e:

        print("Import failed.")
        print(f"Error: {e}")

        raise


if __name__ == "__main__":

    session = next(get_session())

    try:
        import_businesses(session)
    finally:
        session.close()
