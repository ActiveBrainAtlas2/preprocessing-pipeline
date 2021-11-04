from lib.UrlGenerator import UrlGenerator
generator = UrlGenerator()
test_url = '''{
  "dimensions": {
    "x": [
      3.25e-7,
      "m"
    ],
    "y": [
      3.25e-7,
      "m"
    ],
    "z": [
      0.00002,
      "m"
    ]
  },
  "position": [
    31585.580078125,
    18863.2578125,
    309.94189453125
  ],
  "crossSectionOrientation": [
    0,
    0.0998334139585495,
    0,
    0.9950041770935059
  ],
  "crossSectionScale": 48.50858148843085,
  "projectionOrientation": [
    -0.01200499851256609,
    -0.10774974524974823,
    -0.04066292196512222,
    0.9932735562324524
  ],
  "projectionScale": 50279.60913761768,
  "layers": [
    {
      "type": "image",
      "source": {
        "url": "precomputed://https://activebrainatlas.ucsd.edu/data/DK55/neuroglancer_data/C1",
        "subsources": {
          "default": true,
          "bounds": true
        },
        "enableDefaultSubsources": false
      },
      "tab": "source",
      "shaderControls": {
        "normalized": {
          "range": [
            32892,
            630
          ]
        }
      },
      "name": "C1"
    },
    {
      "type": "annotation",
      "source": {
        "url": "local://annotations",
        "transform": {
          "outputDimensions": {
            "x": [
              3.25e-7,
              "m"
            ],
            "y": [
              3.25e-7,
              "m"
            ],
            "z": [
              0.00002,
              "m"
            ]
          }
        }
      },
      "annotations": [
        {
          "point": [
            41008,
            17375,
            134
          ],
          "type": "point",
          "id": "wzzcvcyn5tbpgkouher4ima49etc8e4vkol5auws",
          "description": "DC_L"
        },
        {
          "point": [
            34813,
            15796,
            144
          ],
          "type": "point",
          "id": "j41ocxacbuzsyuiqfrexp1y2yty5ha6hj7axwbs6",
          "description": "PBG_L"
        },
        {
          "point": [
            37491,
            19216,
            170
          ],
          "type": "point",
          "id": "ejjy1ueg6zwie69ynhl3m5k9rqae66c2w0acyhsa",
          "description": "5N_L"
        },
        {
          "point": [
            40248,
            22534,
            184
          ],
          "type": "point",
          "id": "th5ary6o6iqpfca1xfn1hbjo1nnuplq7jq8ohi9h",
          "description": "7N_L"
        },
        {
          "point": [
            42208,
            21956,
            184
          ],
          "type": "point",
          "id": "vy0qc2cv3yghzjifwduqv8ch2h7zxrn6yhw7vodb",
          "description": "Amb_L"
        },
        {
          "point": [
            44755,
            22643,
            184
          ],
          "type": "point",
          "id": "4u4bbmqw8xlyz0usvrwdh75i66nb76kpyqgb9t01",
          "description": "LRt_L"
        },
        {
          "point": [
            38720,
            16338,
            198
          ],
          "type": "point",
          "id": "xsewf8zpjcehd5ycqfwr8d3vi8ko1p1okxn8t37e",
          "description": "LC_L"
        },
        {
          "point": [
            33530,
            22799,
            214
          ],
          "type": "point",
          "id": "tdbsdca4d2meho8nhim6wwyecbgra24t77s0tbev",
          "description": "Pn_L"
        },
        {
          "point": [
            36952,
            23494,
            224
          ],
          "type": "point",
          "id": "hleo1oajb26svxq7izidy12y3uico2nwc4bbpsoe",
          "description": "Tz_L"
        },
        {
          "point": [
            39224,
            19125,
            226
          ],
          "type": "point",
          "id": "i2wqlb4r2e0aaee2gumsmzhfigzg4odsgn8ug7as",
          "description": "6N_L"
        },
        {
          "point": [
            34485,
            15402,
            232
          ],
          "type": "point",
          "id": "v1wsl5a9qzvv6hph1u05lxg5ify3y4eq2zsw3vbj",
          "description": "3N_L"
        },
        {
          "point": [
            44055,
            18242,
            234
          ],
          "type": "point",
          "id": "j05knq50jsfo3s94txnbwc136tikj578hbpo1cor",
          "description": "10N_L"
        },
        {
          "point": [
            34378,
            15264,
            246
          ],
          "type": "point",
          "id": "7aq6y1yzpnr5alauy3tvzjkngg1mytestwt50xhy",
          "description": "3N_R"
        },
        {
          "point": [
            39052,
            18999,
            262
          ],
          "type": "point",
          "id": "nhvaz2h9g89sw65fi83rwye6pkq9z1edooojqjgt",
          "description": "6N_R"
        },
        {
          "point": [
            44095,
            18266,
            262
          ],
          "type": "point",
          "id": "tz7kaf9ldaird3293bdeab4s51eqarf8tpqtht56",
          "description": "10N_R"
        },
        {
          "point": [
            36972,
            23292,
            274
          ],
          "type": "point",
          "id": "x374qijzx04pf55b3oqrc0e8clyaoxon3aw2ifw7",
          "description": "Tz_R"
        },
        {
          "point": [
            34104,
            22836,
            280
          ],
          "type": "point",
          "id": "p1thn3su55rhslbvia7ohjic3s745m0r00d18dd1",
          "description": "Pn_R"
        },
        {
          "point": [
            39015,
            16056,
            284
          ],
          "type": "point",
          "id": "9dacwo1kxi7emmjkn8xh9ujlgeffb1lcuxn2ysod",
          "description": "LC_R"
        },
        {
          "point": [
            45686,
            22231,
            314
          ],
          "type": "point",
          "id": "sl74ixpk5fubdj0vophwxeltx18l8tyb0zm7oxmr",
          "description": "LRt_R"
        },
        {
          "point": [
            39776,
            22104,
            316
          ],
          "type": "point",
          "id": "mmq16w4umqj277odf9cf33rekmlohssndg2l8771",
          "description": "7N_R"
        },
        {
          "point": [
            37535,
            18496,
            317
          ],
          "type": "point",
          "id": "x2d3qqx418e4pwo2jteqg1e5jcl994r798vqooir",
          "description": "5N_R"
        },
        {
          "point": [
            42416,
            21136,
            318
          ],
          "type": "point",
          "id": "tp2feokf1xg2djp9zgxefb5n7x8edyfumz9wbcwa",
          "description": "Amb_R"
        },
        {
          "point": [
            34797,
            15128,
            338
          ],
          "type": "point",
          "id": "xiem5zm6octq4mmee8byeui5ka4ibb4ld1uazpvr",
          "description": "PBG_R"
        },
        {
          "point": [
            41029,
            16258,
            354
          ],
          "type": "point",
          "id": "hmdwsmfu8z2k6p26n80lu087s49ez6y4cjpgvcfs",
          "description": "DC_R"
        }
      ],
      "shaderControls": {
        "size": 7
      },
      "name": "Manual"
    },
    {
      "type": "annotation",
      "source": {
        "url": "local://annotations",
        "transform": {
          "outputDimensions": {
            "x": [
              3.25e-7,
              "m"
            ],
            "y": [
              3.25e-7,
              "m"
            ],
            "z": [
              0.00002,
              "m"
            ]
          }
        }
      },
      "annotationColor": "#00fffb",
      "annotations": [
        {
          "point": [
            38659,
            18999,
            116
          ],
          "type": "point",
          "id": "bivc2orml0q3ab866zyadyk15aodh9fw06ja8nzs",
          "description": "VCA_L"
        },
        {
          "point": [
            40251,
            19289,
            125
          ],
          "type": "point",
          "id": "dw7s9l33lx53galhfcejhf4ibjymjg7a7qvexwi6",
          "description": "VCP_L"
        },
        {
          "point": [
            40467,
            17165,
            135
          ],
          "type": "point",
          "id": "lwkua3bm2yytpq2s6ev7e4p4406k7e18yccbs93r",
          "description": "DC_L"
        },
        {
          "point": [
            35037,
            15345,
            142
          ],
          "type": "point",
          "id": "qtvdj8s3kjxy4vpedthmm741m61aw4z25ae1wia7",
          "description": "PBG_L"
        },
        {
          "point": [
            41594,
            20176,
            151
          ],
          "type": "point",
          "id": "ju4v74umnwv5pkq6gvtazzthb8fgb7bpbyfy6aoc",
          "description": "Sp5O_L"
        },
        {
          "point": [
            43626,
            19766,
            153
          ],
          "type": "point",
          "id": "f3vq4oz461t4tihifvfacyx24qxm3z26hav2czv7",
          "description": "Sp5I_L"
        },
        {
          "point": [
            33333,
            19382,
            159
          ],
          "type": "point",
          "id": "74i28bkf9prv1ut7h6s3ep9fav9huwrk2kit8wna",
          "description": "SNR_L"
        },
        {
          "point": [
            35570,
            20243,
            159
          ],
          "type": "point",
          "id": "ot1giy1deikghyat1ki4l3pn672dtoavhi3h62vb",
          "description": "VLL_L"
        },
        {
          "point": [
            32509,
            19704,
            168
          ],
          "type": "point",
          "id": "ezcyefclsq53douokvzkjzrtmiozvpoaw94gt2i2",
          "description": "SNC_L"
        },
        {
          "point": [
            37532,
            19300,
            170
          ],
          "type": "point",
          "id": "b2fi4pjnm1sj9izcdp44illd5582vptkrgruo3a8",
          "description": "5N_L"
        },
        {
          "point": [
            40212,
            22671,
            184
          ],
          "type": "point",
          "id": "5ws1eqkl0yjfbqup4wqbyuztcucxqqgcy0xc6qj7",
          "description": "7N_L"
        },
        {
          "point": [
            42288,
            21841,
            184
          ],
          "type": "point",
          "id": "a0b9nhsbkds7nj011r8sc48acj6olsxh1ta1nkjo",
          "description": "Amb_L"
        },
        {
          "point": [
            45873,
            20277,
            186
          ],
          "type": "point",
          "id": "hte2rysq50mzoc0h8kqy0z2ohyvmux6t3lbclje7",
          "description": "Sp5C_L"
        },
        {
          "point": [
            38801,
            20327,
            187
          ],
          "type": "point",
          "id": "4z1ijb4xtpmxd6331r26lk6vm99cf3zsuhkikht4",
          "description": "7n_L"
        },
        {
          "point": [
            44561,
            22846,
            194
          ],
          "type": "point",
          "id": "jiyzlkl87smuqyw00m5fc3eetajfro2gq1dcl5c1",
          "description": "LRt_L"
        },
        {
          "point": [
            38174,
            16938,
            200
          ],
          "type": "point",
          "id": "2r7macaxs7yr46600bxs6yi0pj9e37zxbipcxyis",
          "description": "LC_L"
        },
        {
          "point": [
            34860,
            22997,
            205
          ],
          "type": "point",
          "id": "4eiy2gqksjg3zzxri7rne8knxqwblutqtfijfp0v",
          "description": "Pn_L"
        },
        {
          "point": [
            37621,
            23338,
            212
          ],
          "type": "point",
          "id": "cvbiaj42cb970htpbm29oghfrzpcy9datjvgk60v",
          "description": "Tz_L"
        },
        {
          "point": [
            35365,
            15788,
            226
          ],
          "type": "point",
          "id": "x6ro3fuy28x1ya2ffkl2rqz9221oarifbnbmouku",
          "description": "4N_L"
        },
        {
          "point": [
            39224,
            19098,
            226
          ],
          "type": "point",
          "id": "ft1mndcg9qiwriqljxcxk3urhdhzrxkwnbbwlbgz",
          "description": "6N_L"
        },
        {
          "point": [
            34432,
            15813,
            230
          ],
          "type": "point",
          "id": "sh51fb44geaciyeod2oxofxiov9niu1z02b9n0lz",
          "description": "3N_L"
        },
        {
          "point": [
            35976,
            21547,
            235
          ],
          "type": "point",
          "id": "pymkx9icvait11id8xpkwytmpjqma1dcyoyssgpv",
          "description": "RtTg"
        },
        {
          "point": [
            44314,
            19208,
            239
          ],
          "type": "point",
          "id": "nf4tr3088gcxaf06m86wf4auue55lrl2fhqkrnae",
          "description": "10N_L"
        },
        {
          "point": [
            33718,
            11202,
            241
          ],
          "type": "point",
          "id": "75shl9l4kvxauqjdqmqfhqh3jaqnyd4eox4ynblw",
          "description": "SC"
        },
        {
          "point": [
            34446,
            15756,
            245
          ],
          "type": "point",
          "id": "8h8n617mfkwvm2it40zdotuul7yao389px7va653",
          "description": "3N_R"
        },
        {
          "point": [
            36912,
            10233,
            246
          ],
          "type": "point",
          "id": "4j0mxs9poqsbk2ocni89nacuorm10vu1zepotic8",
          "description": "IC"
        },
        {
          "point": [
            35390,
            15687,
            253
          ],
          "type": "point",
          "id": "4u516gu3dgz9x5eam7f6zi7r6lhxnwm55du560bq",
          "description": "4N_R"
        },
        {
          "point": [
            44300,
            19844,
            253
          ],
          "type": "point",
          "id": "gh3ehm2ue0q58nqlmotx0hr9or3p316cgymo0k2n",
          "description": "12N"
        },
        {
          "point": [
            44148,
            18390,
            256
          ],
          "type": "point",
          "id": "piosybki5x5qhvqe1ehv44c4tk21y1fwcr5xyleu",
          "description": "AP"
        },
        {
          "point": [
            34915,
            22774,
            263
          ],
          "type": "point",
          "id": "hgn06jk7gsjxbajb3hz4jxclmkkoiny3e9q2g90p",
          "description": "Pn_R"
        },
        {
          "point": [
            39259,
            18956,
            263
          ],
          "type": "point",
          "id": "xwebkdewxc39wtocc29hwq1r98h1vnfcpr24151c",
          "description": "6N_R"
        },
        {
          "point": [
            37672,
            23132,
            266
          ],
          "type": "point",
          "id": "2rsjxs6wa6l3l0h0knhkn1tt860p7ho4uqdemvyk",
          "description": "Tz_R"
        },
        {
          "point": [
            44342,
            19091,
            270
          ],
          "type": "point",
          "id": "nxvcf3x6l6x7zoqk4q5ugtxrnbzmt4wruhozhi0r",
          "description": "10N_R"
        },
        {
          "point": [
            38258,
            16598,
            289
          ],
          "type": "point",
          "id": "ys26osxi9by8qmqa88uleotn4af63fqhdoilzb2z",
          "description": "LC_R"
        },
        {
          "point": [
            32630,
            19213,
            296
          ],
          "type": "point",
          "id": "e2vvc34k00rif2nyg5tqa6nhv0fgcdh0n53ijmfc",
          "description": "SNC_R"
        },
        {
          "point": [
            38909,
            19889,
            300
          ],
          "type": "point",
          "id": "8dwpsnrq5ap695cy151kk4s4io717lup3545y2ro",
          "description": "7n_R"
        },
        {
          "point": [
            40327,
            22205,
            305
          ],
          "type": "point",
          "id": "asco8abrh9i6dpacynjd0haiv4z2s4lieqtz15pr",
          "description": "7N_R"
        },
        {
          "point": [
            33474,
            18810,
            308
          ],
          "type": "point",
          "id": "5e70gjg7ewnuyoomxrzw8uo0p0ldkredmxn04zkm",
          "description": "SNR_R"
        },
        {
          "point": [
            44673,
            22392,
            312
          ],
          "type": "point",
          "id": "kvttuev3vj904jv53a9ysdok1rj6dy86iuzoxndr",
          "description": "LRt_R"
        },
        {
          "point": [
            37669,
            18748,
            313
          ],
          "type": "point",
          "id": "1s6ydlnp6cg2r8k1cns3iw8b7xs8fjkn8vua0ced",
          "description": "5N_R"
        },
        {
          "point": [
            42411,
            21342,
            314
          ],
          "type": "point",
          "id": "5uzx6z68n6pz4jb0csr5fmh5rqfsxzbuuv3qiqih",
          "description": "Amb_R"
        },
        {
          "point": [
            35718,
            19642,
            315
          ],
          "type": "point",
          "id": "tuvzuc9cfh343ex77rpes9uw7m486jw5ypwz1ae1",
          "description": "VLL_R"
        },
        {
          "point": [
            46007,
            19734,
            328
          ],
          "type": "point",
          "id": "q75a5fnks5ucsikkdp6o9883um5b3aphknlbgtyw",
          "description": "Sp5C_R"
        },
        {
          "point": [
            35223,
            14590,
            338
          ],
          "type": "point",
          "id": "praoz84i6lh84sorv557sovtgjylb2sv4w2l9nkd",
          "description": "PBG_R"
        },
        {
          "point": [
            41781,
            19422,
            347
          ],
          "type": "point",
          "id": "3qc30222o059mjz2afwyosq0vbrnccrzzpwf0khd",
          "description": "Sp5O_R"
        },
        {
          "point": [
            43817,
            18991,
            354
          ],
          "type": "point",
          "id": "we3idncps04zbajws4bv347n4r6e8brbllfd8cg7",
          "description": "Sp5I_R"
        },
        {
          "point": [
            40683,
            16289,
            363
          ],
          "type": "point",
          "id": "1tm9zoo6pa1j0drx6np791ug3d5aw840yg5jmv26",
          "description": "DC_R"
        },
        {
          "point": [
            40482,
            18352,
            369
          ],
          "type": "point",
          "id": "mf1g8bx36smcrp0nrzh8wrbj1vn1m7jtxis7e9m9",
          "description": "VCP_R"
        },
        {
          "point": [
            38903,
            18013,
            372
          ],
          "type": "point",
          "id": "krdj06j8lampw6c3hert292oxz2hyxmp5n8slvp6",
          "description": "VCA_R"
        }
      ],
      "shaderControls": {
        "size": 8.1
      },
      "name": "Affine Transformed Atlas Com"
    },
    {
      "type": "annotation",
      "source": {
        "url": "local://annotations",
        "transform": {
          "outputDimensions": {
            "x": [
              3.25e-7,
              "m"
            ],
            "y": [
              3.25e-7,
              "m"
            ],
            "z": [
              0.00002,
              "m"
            ]
          }
        }
      },
      "tool": "annotatePoint",
      "annotationColor": "#6600ff",
      "annotations": [
        {
          "point": [
            38133.41796875,
            18458.037109375,
            121.81912994384766
          ],
          "type": "point",
          "id": "ab4eb384169b2066399ca99b8a83c4e220762893",
          "description": "VCA_L\n\n\n\n"
        },
        {
          "point": [
            38182.203125,
            17433.193359375,
            366.5
          ],
          "type": "point",
          "id": "bafbb3b1d20e17f6633da41211bfe6755909707f",
          "description": "VCA_R\n"
        },
        {
          "point": [
            39961.4140625,
            19770.984375,
            125.5
          ],
          "type": "point",
          "id": "59f4d7eca80d9122bd3c958fd9f2e0e3f03e289e",
          "description": "VCP_L\n\n\n"
        },
        {
          "point": [
            40116.33984375,
            19173.310546875,
            367.7767028808594
          ],
          "type": "point",
          "id": "12653e5bc347f1635f9a620511e6ad854f7d90a7",
          "description": "VCP_R\n\n"
        },
        {
          "point": [
            44004.22265625,
            19296.734375,
            149.49998474121094
          ],
          "type": "point",
          "id": "76e4e313898d720b3a4aea1f59b7922c69f11a3a",
          "description": "SP5I_L"
        },
        {
          "point": [
            44255.15625,
            18515.44140625,
            355.5
          ],
          "type": "point",
          "id": "e65c66776d5fbb0c4ebf2c518b377322f782baeb",
          "description": "SP5I_R\n"
        },
        {
          "point": [
            42903.48046875,
            19514.70703125,
            148.5
          ],
          "type": "point",
          "id": "07d57c629e314257e5fce44109a1b99594697966",
          "description": "SP5O_L\n"
        },
        {
          "point": [
            42073.31640625,
            19448.50390625,
            348.5
          ],
          "type": "point",
          "id": "b32e5a075c61c0e70810caed20ce5003ba39f33b",
          "description": "SP5O_R\n"
        },
        {
          "point": [
            34811.171875,
            20127.517578125,
            165.5
          ],
          "type": "point",
          "id": "a1ee16c90e52dbe220f425486d47108d422620ef",
          "description": "VLL_L\n"
        },
        {
          "point": [
            34974.8515625,
            19511.0390625,
            325.3406982421875
          ],
          "type": "point",
          "id": "acc500dc018437e037d6e17924a79f75b4e0493d",
          "description": "VLL_R\n"
        },
        {
          "point": [
            32946.47265625,
            19491.609375,
            170.5
          ],
          "type": "point",
          "id": "ba950f0d51c6bd4f8addc4a824834472672899bf",
          "description": "SNR_L\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        },
        {
          "point": [
            32879.1328125,
            19038.267578125,
            317.5000305175781
          ],
          "type": "point",
          "id": "a961db67af3498a77ec877d402e34b249caa5929",
          "description": "SNR_R\n"
        },
        {
          "point": [
            31453.173828125,
            19465.779296875,
            175.8746337890625
          ],
          "type": "point",
          "id": "54ede63b420a20511c216bab0722e455e34272a1",
          "description": "SNC_L\n\n\n"
        },
        {
          "point": [
            31609.3515625,
            18735.919921875,
            309.86358642578125
          ],
          "type": "point",
          "id": "59ce7bb2d495411610b67d105614f95989da1263",
          "description": "SNC_R\n"
        }
      ],
      "shaderControls": {
        "size": 10
      },
      "name": "additional manual annotations"
    }
  ],
  "selectedLayer": {
    "layer": "additional manual annotations",
    "visible": true
  },
  "layout": "4panel",
  "selection": {
    "layers": {
      "additional manual annotations": {
        "annotationId": "59ce7bb2d495411610b67d105614f95989da1263",
        "annotationSource": 0,
        "annotationSubsource": "default"
      }
    }
  }
}'''
generator.parse_url(test_url)