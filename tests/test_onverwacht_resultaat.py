from tekstherkenning_ark.models.onverwacht_resultaat import OnverwachtResultaat


def test_onverwacht_resultaat_false():
    res = OnverwachtResultaat(waarde="niet gemeten")

    assert bool(res) is False
