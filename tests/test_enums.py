from tekstherkenning_ark.enums import NietBeschikbaar


def test_niet_beschikbaar_falsey():

    assert bool(NietBeschikbaar.NIET_VAN_TOEPASSING) is False
    assert bool(NietBeschikbaar.NIET_MEETBAAR) is False
    assert bool(NietBeschikbaar.LEEG) is False

    if not NietBeschikbaar.NIET_VAN_TOEPASSING:
        assert True
    else:
        assert False, "NietBeschikbaar.NIET_VAN_TOEPASSING should be falsey"
