from src.domain import EXPRESSION_NAMES, Expression, RobotMode


def test_expression_enum_matches_asset_lookup():
    assert len(EXPRESSION_NAMES) == len(Expression)
    assert EXPRESSION_NAMES[Expression.HAPPY] == "happy"
    assert EXPRESSION_NAMES[Expression.ERROR] == "error"


def test_robot_modes_keep_wire_compatible_values():
    assert int(RobotMode.STAND_STILL) == 0
    assert int(RobotMode.FOLLOW) == 1
    assert int(RobotMode.GO_AROUND) == 2
