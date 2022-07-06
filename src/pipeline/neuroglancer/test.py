import json
from AnnotationLayer import AnnotationLayer
layer = '''    {
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
      "annotations": [
        {
          "source": [
            26328.533203125,
            12155.18359375,
            234.5
          ],
          "childAnnotationIds": [
            "8882bf600154597cb465df319ec85fd67588d515",
            "34f85fd4629f9ea3d2c9edfa2e047f94f290f7a7",
            "4f4bcfaf79d52a099808238af3990ba292264bc8",
            "f79140a72ad821cd7f633aabdbd910c8c53188c5",
            "e34c98ad6b2646e7fb0661b8385d4c9389822736"
          ],
          "type": "polygon",
          "id": "f09dd558d91c038bdc7d1b751557780c1c3e514a"
        },
        {
          "pointA": [
            26328.533203125,
            12155.18359375,
            234.5
          ],
          "pointB": [
            30044.357421875,
            11833.8154296875,
            234.5
          ],
          "type": "line",
          "id": "8882bf600154597cb465df319ec85fd67588d515",
          "parentAnnotationId": "f09dd558d91c038bdc7d1b751557780c1c3e514a"
        },
        {
          "pointA": [
            30044.357421875,
            11833.8154296875,
            234.5
          ],
          "pointB": [
            30767.435546875,
            14746.2177734375,
            234.5
          ],
          "type": "line",
          "id": "34f85fd4629f9ea3d2c9edfa2e047f94f290f7a7",
          "parentAnnotationId": "f09dd558d91c038bdc7d1b751557780c1c3e514a"
        },
        {
          "pointA": [
            30767.435546875,
            14746.2177734375,
            234.5
          ],
          "pointB": [
            27573.8359375,
            15830.8369140625,
            234.5
          ],
          "type": "line",
          "id": "4f4bcfaf79d52a099808238af3990ba292264bc8",
          "parentAnnotationId": "f09dd558d91c038bdc7d1b751557780c1c3e514a"
        },
        {
          "pointA": [
            27573.8359375,
            15830.8369140625,
            234.5
          ],
          "pointB": [
            25264,
            15348.7841796875,
            234.5
          ],
          "type": "line",
          "id": "f79140a72ad821cd7f633aabdbd910c8c53188c5",
          "parentAnnotationId": "f09dd558d91c038bdc7d1b751557780c1c3e514a"
        },
        {
          "pointA": [
            25264,
            15348.7841796875,
            234.5
          ],
          "pointB": [
            26328.533203125,
            12155.18359375,
            234.5
          ],
          "type": "line",
          "id": "e34c98ad6b2646e7fb0661b8385d4c9389822736",
          "parentAnnotationId": "f09dd558d91c038bdc7d1b751557780c1c3e514a"
        },
        {
          "source": [
            25665.7109375,
            11070.564453125,
            235.5
          ],
          "childAnnotationIds": [
            "c0724972b320333df4c279033474e05b85ed6d0b",
            "044fcc79c961db5398983bf394a472453f2b3a40",
            "6564ab4f822a5d956502dd09becad75ff6f4d4ed",
            "bdb58eb2f5eb9092a87b89a622f6c0427572af49",
            "b5cc508aa07c78953ec5c92ce4e422b53775f146"
          ],
          "type": "polygon",
          "id": "df4ab700a48342fb82a9e2f80e212fe1ac4b2192"
        },
        {
          "pointA": [
            25665.7109375,
            11070.564453125,
            235.5
          ],
          "pointB": [
            29441.791015625,
            10508.169921875,
            235.5
          ],
          "type": "line",
          "id": "c0724972b320333df4c279033474e05b85ed6d0b",
          "parentAnnotationId": "df4ab700a48342fb82a9e2f80e212fe1ac4b2192"
        },
        {
          "pointA": [
            29441.791015625,
            10508.169921875,
            235.5
          ],
          "pointB": [
            30104.61328125,
            13661.5986328125,
            235.5
          ],
          "type": "line",
          "id": "044fcc79c961db5398983bf394a472453f2b3a40",
          "parentAnnotationId": "df4ab700a48342fb82a9e2f80e212fe1ac4b2192"
        },
        {
          "pointA": [
            30104.61328125,
            13661.5986328125,
            235.5
          ],
          "pointB": [
            26911.013671875,
            14746.2177734375,
            235.5
          ],
          "type": "line",
          "id": "6564ab4f822a5d956502dd09becad75ff6f4d4ed",
          "parentAnnotationId": "df4ab700a48342fb82a9e2f80e212fe1ac4b2192"
        },
        {
          "pointA": [
            26911.013671875,
            14746.2177734375,
            235.5
          ],
          "pointB": [
            24601.177734375,
            14264.1650390625,
            235.5
          ],
          "type": "line",
          "id": "bdb58eb2f5eb9092a87b89a622f6c0427572af49",
          "parentAnnotationId": "df4ab700a48342fb82a9e2f80e212fe1ac4b2192"
        },
        {
          "pointA": [
            24601.177734375,
            14264.1650390625,
            235.5
          ],
          "pointB": [
            25665.7109375,
            11070.564453125,
            235.5
          ],
          "type": "line",
          "id": "b5cc508aa07c78953ec5c92ce4e422b53775f146",
          "parentAnnotationId": "df4ab700a48342fb82a9e2f80e212fe1ac4b2192"
        },
        {
          "point": [
            35065.7421875,
            18110.544921875,
            234.5
          ],
          "type": "point",
          "id": "e2e722f08ca057820c633918ff9850186759035f"
        },
        {
          "point": [
            30425.982421875,
            19014.39453125,
            234.5
          ],
          "type": "point",
          "id": "73717854d8419134031705128c986814e7eb9724"
        },
        {
          "point": [
            21969.970703125,
            18713.111328125,
            234.5
          ],
          "type": "point",
          "id": "8c8c664b23b4ba919aa6e8ee066826e9857bb746"
        }
      ],
      "name": "annotation"
    }'''

layer= json.loads(layer)
layer = AnnotationLayer(layer)
print('done')