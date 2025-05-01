from multiprocessing import freeze_support
from app import create_app

if __name__ == "__main__":
    freeze_support()
    app,server = create_app()
    # server = app.server
    app.run(debug=False)
    # app.run(debug=False)

#
