from flask import (
    Flask,
    render_template,
    redirect,
    request,
    abort,
    jsonify,
    make_response,
)
import os

application = Flask(__name__)
application.config["SECRET_KEY"] = "werty57i39fj92udifkdb56fwed232z"


@application.route("/orders", methods=["POST"])
def get_orders():
    data = request.data
    print(data)
    return make_response(jsonify({"success": True}), 200)


@application.route("/powerstand", methods=["GET"])
def init_powertsand():
    resp = {
        "success": True,
        "conf": {"gameLength": 100},
        "tick": 0,
        "scores": [1, [1, 2]],
        "externalFail": [],
        "weatherWind": [],
        "weatherSun": [],
        "objs": [],
        "nets": [],
        "forecasts": {
            "sfClass1": [],
            "sfClass2": [],
            "sfClass3A": [],
            "sfClass3B": [],
            "sfSun": [],
            "sfWind": [],
        },
        "exchangeReceipts": [],
        "totalPowers": [],
    }
    response = make_response(jsonify(resp), 200)
    return response


def main():
    application.run(port=26000)


if __name__ == "__main__":
    main()
