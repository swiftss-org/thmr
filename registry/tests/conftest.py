import pytest

import config as thmr_config
from registry.schema import Database
from registry.tests import data_generator


@pytest.fixture(scope="module")
def database_session():
    db = Database(thmr_config.Config.DB_TEST_URL)
    db.create_all()
    session = db.create_session()

    with session.begin_nested():
        data_generator.create_sample_data(session,
                                          num_users=12,
                                          num_patients=50)

    yield session

    session.close()
    db.drop_all()