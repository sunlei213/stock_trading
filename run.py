from app import create_app, db, redis_client
from app.models import  Admin
from app.logging_config import logger
import sys

app = create_app()

if __name__ == '__main__':
    av1 = len(sys.argv) > 1
    if av1:
        redis_client.xgroup_create()
        username = input("username:")
        password = input("password:")
        with app.app_context():
            db.drop_all()
            db.create_all()  # make our sqlalchemy tables
            admin = Admin(username=username, password=password)
            db.session.add(admin)
            db.session.commit()
        logger.info("数据库创建成功")

    else:
        logger.info("启动后台服务")
        app.run(host='0.0.0.0',port=8001)
