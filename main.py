from multiprocessing import freeze_support
from app import create_app
import os
from flask import Flask

if '__file__' in globals():
    root_path = os.path.dirname(os.path.abspath(__file__))
else:
    # Fallback for environments where __file__ isn't available
    root_path = os.getcwd()

server = Flask(
        __name__,
        instance_path=os.path.join(root_path, 'instance'),
        root_path=root_path,
        static_folder=os.path.join(root_path, 'assets')
    )

if __name__ == "__main__":
    freeze_support()
    app = create_app(server)
    # server = app.server
    app.run(debug=False)
    # app.run(debug=False)

#
