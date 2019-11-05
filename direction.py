def direction_from_angle(ang):
    """ Convert an angle, like 33.12, to a direction, like 'NNE'
        Large numbers are folded to 0-360, and negative angles
        are subtracted from 360, so -90 is West and 700 is 'NNW'

        Dir    Min      Mid       Max     Dir      Mid       Min     Max
        ---   ------   ------   ------    ---    -------    -----  -------
        N       0        0       11.25    S       168.75    180     191.25
        NNE   >11.25    22.5    <33.75    SSW    >191.25    202.5  <213.75
        NE     33.75    45       56.25    SW      213.75    225     236.25
        ENE   >56.25    67.5    <78.75    WSW    >236.25    247.5  <258.75
        E      79.75    90      101.25    W       258.75    270     281.25
        ESE  >101.25    112.5  <123.75    WNW    >281.25    292.5  <303.75
        SE    123.75    135     146.25    NW      303.75    315     326.25
        SSE  >146.25    157.5  <168.75    NNW    >326.25    337.5  <348.75
    """
    direction_names = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                       'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    nsegs    = len(direction_names)
    seg_size = 360 / nsegs
    ang      = abs(ang % 360)
    assert(0 <= ang <= 360), 'ang = {0},'.format(ang)
    seg      = round(ang / seg_size) % nsegs
    assert(0 <= seg < nsegs)
    return   direction_names[seg]


def test():
    # check for asserts, without printing
    for ang in range(-361, 360 * 2):
        direction_from_angle(ang)

    n1 = direction_from_angle(-11.25)
    n2 = direction_from_angle(0)
    n3 = direction_from_angle(11.25)
    assert(n1 == 'N' and n2 == 'N' and n3 == 'N')
    print(n1, n2, n3)

    nne1 = direction_from_angle(11.25000001)
    nne2 = direction_from_angle(22.5)
    nne3 = direction_from_angle(33.74999999)
    print(nne1, nne2, nne3)
    assert(nne1 == 'NNE' and nne2 == 'NNE' and nne3 == 'NNE')

    ne1 = direction_from_angle(33.75)
    ne2 = direction_from_angle(45)
    ne3 = direction_from_angle(56.25)
    print(ne1, ne2, ne3)
    assert(ne1 == 'NE' and ne2 == 'NE' and ne3 == 'NE')

    ene1 = direction_from_angle(56.25000001)
    ene2 = direction_from_angle(67.5)
    ene3 = direction_from_angle(78.74999999)
    print(ene1, ene2, ene3)
    assert(ene1 == 'ENE' and ene2 == 'ENE' and ene3 == 'ENE')

    e1 = direction_from_angle(79.75)
    e2 = direction_from_angle(90)
    e3 = direction_from_angle(101.25)
    print(e1, e2, e3)
    assert(e1 == 'E' and e2 == 'E' and e3 == 'E')

    ese1 = direction_from_angle(101.25000001)
    ese2 = direction_from_angle(112.5)
    ese3 = direction_from_angle(123.74999999)
    print(ese1, ese2, ese3)
    assert(ese1 == 'ESE' and ese2 == 'ESE' and ese3 == 'ESE')

    se1 = direction_from_angle(123.75)
    se2 = direction_from_angle(135)
    se3 = direction_from_angle(146.25)
    print(se1, se2, se3)
    assert(se1 == 'SE' and se2 == 'SE' and se3 == 'SE')

    sse1 = direction_from_angle(146.25000001)
    sse2 = direction_from_angle(157.5)
    sse3 = direction_from_angle(168.74999999)
    print(sse1, sse2, sse3)
    assert(sse1 == 'SSE' and sse2 == 'SSE' and sse3 == 'SSE')

    s1 = direction_from_angle(168.75)
    s2 = direction_from_angle(180)
    s3 = direction_from_angle(191.25)
    print(s1, s2, s3)
    assert(s1 == 'S' and s2 == 'S' and s3 == 'S')

    ssw1 = direction_from_angle(191.25000001)
    ssw2 = direction_from_angle(202.5)
    ssw3 = direction_from_angle(213.74999999)
    print(ssw1, ssw2, ssw3)
    assert(ssw1 == 'SSW' and ssw2 == 'SSW' and ssw3 == 'SSW')

    sw1 = direction_from_angle(213.75)
    sw2 = direction_from_angle(225)
    sw3 = direction_from_angle(236.25)
    print(sw1, sw2, sw3)
    assert(sw1 == 'SW' and sw2 == 'SW' and sw3 == 'SW')

    wsw1 = direction_from_angle(236.25000001)
    wsw2 = direction_from_angle(247.5)
    wsw3 = direction_from_angle(258.74999999)
    print(wsw1, wsw2, wsw3)
    assert(wsw1 == 'WSW' and wsw2 == 'WSW' and wsw3 == 'WSW')

    w1 = direction_from_angle(258.75)
    w2 = direction_from_angle(270)
    w3 = direction_from_angle(281.25)
    print(w1, w2, w3)
    assert(w1 == 'W' and w2 == 'W' and w3 == 'W')

    wnw1 = direction_from_angle(281.25000001)
    wnw2 = direction_from_angle(292.5)
    wnw3 = direction_from_angle(303.74999999)
    print(wnw1, wnw2, wnw3)
    assert(wnw1 == 'WNW' and wnw2 == 'WNW' and wnw3 == 'WNW')

    nw1 = direction_from_angle(303.75)
    nw2 = direction_from_angle(315)
    nw3 = direction_from_angle(326.25)
    print(nw1, nw2, nw3)
    assert(nw1 == 'NW' and nw2 == 'NW' and nw3 == 'NW')

    nnw1 = direction_from_angle(326.25000001)
    nnw2 = direction_from_angle(337.5)
    nnw3 = direction_from_angle(348.74999999)
    print(nnw1, nnw2, nnw3)
    assert(nnw1 == 'NNW' and nnw2 == 'NNW' and nnw3 == 'NNW')


test()
