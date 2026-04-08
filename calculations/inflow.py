import numpy as np

class Inflow:
    """Расчет притока газа к скважине"""

    @staticmethod
    def Q_gas(P_pl, P_zab, a, b):
        """
        Расчет дебита скважины по двучленной формуле

        P_pl² - P_zab² = a * Q + b * Q²

        Параметры:
        ----------
        P_pl : float
            Пластовое давление (МПа)
        P_zab : float
            Забойное давление (МПа)
        a : float
            Коэффициент ламинарного сопротивления (МПа²/(тыс.м³/сут))
        b : float
            Коэффициент турбулентного сопротивления (МПа²/(тыс.м³/сут)²)

        Возвращает:
        -----------
        Q : float
            Дебит скважины (тыс.м³/сут)
        """
        if P_zab <= 0:
            return 0.0

        dP2 = P_pl ** 2 - P_zab ** 2

        if dP2 <= 0:
            return 0.0

        if b == 0:
            return dP2 / a

        # Решение квадратного уравнения: b*Q² + a*Q - dP2 = 0
        D = a ** 2 + 4 * b * dP2

        if D <= 0:
            return 0.0

        Q = (-a + np.sqrt(D)) / (2 * b)

        return max(0, Q)

    @staticmethod
    def a_coeff_from_params(k, h, mu, Z, r_skv, r_k, skin):
        """
        Расчет коэффициента a по параметрам пласта

        k : проницаемость (мД)
        h : толщина (м)
        mu : вязкость (сПз)
        Z : коэффициент сверхсжимаемости
        r_skv : радиус скважины (м)
        r_k : радиус контура питания (м)
        skin : скин-фактор
        """
        kh = k * h  # мД·м
        factor = 7.7677e-3  # пересчетный коэффициент

        a = factor * (mu * Z) / kh * (np.log(r_k / r_skv) + skin)

        return a
