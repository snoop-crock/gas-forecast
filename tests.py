import unittest

from calculations.forecast import calculate_forecast, default_params
from calculations.scenario import RECOVERY_RATE_COLUMN, WELLS_COLUMN, build_yearly_schedule


class ForecastTests(unittest.TestCase):
    def test_basic_forecast_returns_rows(self):
        params = default_params.copy()
        params.update(
            {
                "start_year": 2025,
                "T_max": 2,
                "plateau_mode": "manual",
                "target_recovery_rate": 1.0,
                "Q_polka": 0,
            }
        )

        result = calculate_forecast(params)

        self.assertTrue(result["monthly_df"])
        self.assertTrue(result["yearly_df"])
        self.assertEqual(len(result["wells_schedule"]), 2)
        self.assertEqual(len(result["recovery_schedule"]), 2)

    def test_advanced_schedule_affects_yearly_outputs(self):
        params = default_params.copy()
        params.update(
            {
                "start_year": 2025,
                "T_max": 3,
                "plateau_mode": "manual",
                "target_recovery_rate": 1.0,
                "Q_polka": 0,
                "wells_schedule": [
                    {"Год": 2025, WELLS_COLUMN: 5},
                    {"Год": 2026, WELLS_COLUMN: 8},
                    {"Год": 2027, WELLS_COLUMN: 12},
                ],
                "recovery_schedule": [
                    {"Год": 2025, RECOVERY_RATE_COLUMN: 1.0},
                    {"Год": 2026, RECOVERY_RATE_COLUMN: 2.5},
                    {"Год": 2027, RECOVERY_RATE_COLUMN: 1.5},
                ],
            }
        )

        result = calculate_forecast(params)
        yearly = {row["Год"]: row for row in result["yearly_df"]}

        self.assertEqual(yearly[2025]["Количество скважин"], 5)
        self.assertEqual(yearly[2026]["Количество скважин"], 8)
        self.assertEqual(yearly[2027]["Количество скважин"], 12)
        self.assertAlmostEqual(yearly[2026]["Целевой темп отбора, %"], 2.5, places=2)
        self.assertAlmostEqual(yearly[2027]["Целевой темп отбора, %"], 1.5, places=2)

    def test_schedule_values_are_carried_forward_until_next_change(self):
        wells_schedule = build_yearly_schedule(
            start_year=2025,
            horizon_years=5,
            default_value=10,
            value_column=WELLS_COLUMN,
            raw_schedule=[
                {"Год": 2029, WELLS_COLUMN: 30},
                {"Год": 2031, WELLS_COLUMN: 60},
            ],
            cast_type=int,
        )
        recovery_schedule = build_yearly_schedule(
            start_year=2025,
            horizon_years=5,
            default_value=1.0,
            value_column=RECOVERY_RATE_COLUMN,
            raw_schedule=[
                {"Год": 2029, RECOVERY_RATE_COLUMN: 3.5},
                {"Год": 2031, RECOVERY_RATE_COLUMN: 5.0},
            ],
            cast_type=float,
        )

        self.assertEqual([row[WELLS_COLUMN] for row in wells_schedule], [10, 10, 10, 10, 30])
        self.assertEqual([row[RECOVERY_RATE_COLUMN] for row in recovery_schedule], [1.0, 1.0, 1.0, 1.0, 3.5])

        continued_wells_schedule = build_yearly_schedule(
            start_year=2029,
            horizon_years=5,
            default_value=10,
            value_column=WELLS_COLUMN,
            raw_schedule=[
                {"Год": 2029, WELLS_COLUMN: 30},
                {"Год": 2032, WELLS_COLUMN: 60},
            ],
            cast_type=int,
        )

        self.assertEqual([row[WELLS_COLUMN] for row in continued_wells_schedule], [30, 30, 30, 60, 60])


if __name__ == "__main__":
    unittest.main()
