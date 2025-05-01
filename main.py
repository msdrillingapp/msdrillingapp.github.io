from multiprocessing import freeze_support
from app import create_app

if __name__ == "__main__":
    freeze_support()
    app = create_app()
    app.run(debug=True)
    # app.run(debug=False)

#
