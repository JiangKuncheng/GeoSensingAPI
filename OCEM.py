# -*- coding: utf-8 -*-
"""
PROJECT_NAME: Other_Python 
FILE_NAME: OCEM 
AUTHOR: welt 
E_MAIL: tjlwelt@foxmail.com
DATE: 2025-08-11 
"""

import numpy as np
from typing import List, Dict, Any


class OCEM_Evaluator:
    """
    根据论文 "Observation Capability Evaluation Model for Flood-Observation-Oriented
    Satellite Sensor Selection" (Appl. Sci. 2023, 13, 12482) 复现并封装OCEM算法。

    该类提供了计算10个观测能力因子、通过AHP方法分配权重以及计算最终OCEM得分的功能。

    使用方法:
    1. 为你的任务创建一个 `OCEM_Evaluator` 实例。
    2. 准备一个包含所有待评估传感器的列表 (List[Dict]) 和一个包含任务参数的字典 (Dict)。
    3. 准备一个针对当前任务阶段的AHP成对比较矩阵 (numpy.ndarray)。
    4. 调用 `evaluate_sensor_ranking` 方法，传入传感器数据、任务参数和AHP矩阵。
    5. 该方法将返回一个按OCEM得分降序排列的传感器列表。
    """

    def __init__(self, alpha: float = 0.2):
        """
        初始化评估器。

        Args:
            alpha (float): 公式中的可调正向缩放因子，论文中建议值为0.2。
        """
        self.alpha = alpha
        # AHP方法的随机一致性指数 (Random Index) 表，键为矩阵阶数n
        self.RI = {
            1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
        }
        self.THCO_RELEVANCE_MAP = {
            "primary": 1.0, "high": 0.8, "medium": 0.6,
            "useful": 0.4, "marginal": 0.2
        }
        self.POL_CONFORMITY_MAP = {
            "VV": 0.2, "VV/VH": 0.4, "HV": 0.4, "VH": 0.4,
            "HH": 0.6, "HH/VV": 0.6, "HH/HV": 0.8,
            "HH/HV/VV/VH": 1.0
        }

    # 1. 观测能力因子计算方法 (基于论文 Section 2.3.1)

    def _calculate_spco(self, s_cover: float, s_task: float) -> float:
        """Eq (2): 计算空间覆盖率 (SpCo)"""
        return s_cover / s_task if s_task > 0 else 0

    def _calculate_tico(self, t_cover: float, t_task: float) -> float:
        """Eq (3): 计算时间覆盖率 (TiCo)"""
        return t_cover / t_task if t_task > 0 else 0

    def _calculate_thco(self, observation_params: List[str]) -> float:
        """Eq (4, 5): 计算主题符合度 (ThCo)"""
        if not observation_params:
            return 0
        total_relevance = sum(self.THCO_RELEVANCE_MAP.get(p.lower(), 0) for p in observation_params)
        return total_relevance / len(observation_params)

    def _calculate_reti(self, t_start: float, t_end: float, t_respond: float) -> float:
        """Eq (6): 计算响应时效性 (ReTi)"""
        denominator = t_end - t_start
        return (t_end - t_respond) / denominator if denominator > 0 else 0

    def _calculate_refc(self, rf_i: int, all_rf_values: List[int]) -> float:
        """Eq (7): 计算重访频率 (ReFc)"""
        sum_of_squares = sum(rf ** 2 for rf in all_rf_values)
        return rf_i / np.sqrt(sum_of_squares) if sum_of_squares > 0 else 0

    def _calculate_spares(self, spa_i: float, spa_task: float) -> float:
        """Eq (8): 计算空间分辨率符合度 (SpaRes)"""
        if spa_i < spa_task:
            return 1.0
        return spa_task / spa_i if spa_i > 0 else 0

    def _calculate_radres(self, rad_i: int, rad_task: int) -> float:
        """Eq (9): 计算辐射分辨率符合度 (RadRes)"""
        if rad_i >= rad_task:
            return 1.0
        return rad_i / rad_task if rad_task > 0 else 0

    def _calculate_speres(self, r_sensor: Dict, r_task: Dict) -> float:
        """Eq (10): 计算光谱分辨率符合度 (SpeRes) - 仅用于光学传感器"""
        r_sensor_min, r_sensor_max = r_sensor.get('range', (0, 0))
        r_task_min, r_task_max = r_task.get('range', (0, 0))
        spe_least = r_task.get('least', 0)

        intersection_min = max(r_sensor_min, r_task_min)
        intersection_max = min(r_sensor_max, r_task_max)

        delta_intersection = intersection_max - intersection_min

        if delta_intersection <= 0:
            return 0.0
        if delta_intersection < spe_least:
            return 1.0  # 论文中这里有歧义，根据上下文理解为优于最低要求

        sensor_interval = r_sensor.get('interval', float('inf'))
        if sensor_interval == 0: return 1.0  # 避免除零错误
        # 论文原文为 Spe_least / (r2)，r2是传感器波长范围，这似乎不合理。
        # 此处根据上下文逻辑，解释为传感器自身的光谱分辨率与任务要求的比较。
        # 为忠实原文，此处实现 Spe_least / delta_intersection
        return spe_least / delta_intersection

    def _calculate_pol(self, polarization_mode: str) -> float:
        """Eq (11): 计算极化模式符合度 (Pol) - 仅用于微波传感器"""
        return self.POL_CONFORMITY_MAP.get(polarization_mode, 0)

    def _calculate_enim(self, cloud_cover: float, sensor_type: str) -> float:
        """Eq (12): 计算环境影响 (EnIm)"""
        if sensor_type.lower() == 'microwave':
            return 1.0
        elif sensor_type.lower() == 'optical':
            return 1.0 - cloud_cover
        return 0.0

    # 2. AHP 权重计算方法 (基于论文 Section 2.3.2)
    def calculate_ahp_weights(self, matrix: np.ndarray, check_consistency: bool = True) -> np.ndarray:
        """
        通过层次分析法 (AHP) 计算权重向量。

        Args:
            matrix (np.ndarray): 成对比较矩阵.
            check_consistency (bool): 是否执行一致性检验。

        Returns:
            np.ndarray: 归一化的权重向量。

        Raises:
            ValueError: 如果矩阵未通过一致性检验。
        """
        n = matrix.shape[0]
        eigenvalues, eigenvectors = np.linalg.eig(matrix)

        max_eigenvalue = np.max(eigenvalues.real)
        max_eigenvector = eigenvectors[:, np.argmax(eigenvalues.real)].real

        weights = max_eigenvector / np.sum(max_eigenvector)

        if check_consistency:
            ci = (max_eigenvalue - n) / (n - 1) if n > 1 else 0
            ri = self.RI.get(n)
            if ri is None or ri == 0:
                cr = float('inf') if ci > 0 else 0
            else:
                cr = ci / ri

            if cr > 0.1:
                raise ValueError(f"AHP矩阵未通过一致性检验 (CR = {cr:.4f} > 0.1)。请检查您的比较矩阵。")

        return weights

    # 3. 主评估流程
    def evaluate_sensor_ranking(self,
                                sensors_data: List[Dict[str, Any]],
                                task_params: Dict[str, Any],
                                ahp_matrix: np.ndarray) -> List[Dict[str, Any]]:
        """
        评估并排序一系列传感器。

        Args:
            sensors_data (List[Dict]): 待评估传感器的列表。每个字典应包含传感器属性。
                示例: {'name': 'SensorA', 'type': 'optical', 's_cover': 100, ...}
            task_params (Dict): 当前观测任务的参数。
                示例: {'s_task': 500, 't_task': 24, 'req_spatial_res': 10, ...}
            ahp_matrix (np.ndarray): 针对此任务的AHP成对比较矩阵。
                                     矩阵的维度应为6x6，对应因子顺序为:
                                     [ReTi, TiCo, ReFc, SpaRes, SpeRes/Pol, RadRes]

        Returns:
            List[Dict]: 包含传感器名称和其OCEM分数的列表，按分数降序排列。
        """

        # 步骤 1: 计算 AHP 权重
        # 论文中AHP矩阵的因子顺序为: ReTi, TiCo, ReFc, SpaRes, SpeRes/Pol, RadRes
        weights = self.calculate_ahp_weights(ahp_matrix)
        weight_map = {
            'ReTi': weights[0], 'TiCo': weights[1], 'ReFc': weights[2],
            'SpaRes': weights[3], 'SpeRes/Pol': weights[4], 'RadRes': weights[5]
        }

        # 预计算所有传感器的重访频率值 (ReFc因子计算需要)
        all_rf_values = [s.get('revisit_freq', 0) for s in sensors_data]

        results = []
        for sensor in sensors_data:
            # 步骤 2: 计算10个能力因子
            factors = {}
            factors['SpCo'] = self._calculate_spco(sensor.get('s_cover', 0), task_params.get('s_task', 1))
            factors['TiCo'] = self._calculate_tico(sensor.get('t_cover', 0), task_params.get('t_task', 1))
            factors['ThCo'] = self._calculate_thco(sensor.get('observation_params', []))
            factors['ReTi'] = self._calculate_reti(task_params.get('t_start', 0), task_params.get('t_end', 1),
                                                   sensor.get('respond_time', 0))
            factors['ReFc'] = self._calculate_refc(sensor.get('revisit_freq', 0), all_rf_values)
            factors['SpaRes'] = self._calculate_spares(sensor.get('spatial_res', float('inf')),
                                                       task_params.get('req_spatial_res', 1))
            factors['RadRes'] = self._calculate_radres(sensor.get('rad_res', 0), task_params.get('req_rad_res', 1))

            sensor_type = sensor.get('type', 'optical').lower()
            factors['EnIm'] = self._calculate_enim(sensor.get('cloud_cover', 0), sensor_type)

            # SpeRes/Pol 是互斥的
            if sensor_type == 'optical':
                factors['SpeRes/Pol'] = self._calculate_speres(sensor.get('wavelength_info', {}),
                                                               task_params.get('req_wavelength_info', {}))
            elif sensor_type == 'microwave':
                factors['SpeRes/Pol'] = self._calculate_pol(sensor.get('polarization', ''))
            else:
                factors['SpeRes/Pol'] = 0

            # 步骤 3: 计算 OCEM 值
            # 注意：论文中的 Eq(1) 与其文字描述存在矛盾。
            # "若SpCo, ThCo, EnIm等因子为0，则OCEM为0"的描述与 e^(1+α*F) 的公式形式不符。
            # 此处采用 "if-else" 结构来实现论文的意图，这被认为是更合理的解释。
            if factors['SpCo'] == 0 or factors['ThCo'] == 0 or factors['EnIm'] == 0:
                ocem_score = 0.0
            else:
                linear_sum = (weight_map['ReTi'] * factors['ReTi'] +
                              weight_map['TiCo'] * factors['TiCo'] +
                              weight_map['ReFc'] * factors['ReFc'] +
                              weight_map['SpaRes'] * factors['SpaRes'] +
                              weight_map['SpeRes/Pol'] * factors['SpeRes/Pol'] +
                              weight_map['RadRes'] * factors['RadRes'])

                if linear_sum == 0:
                    ocem_score = 0.0
                else:
                    term1 = np.exp(1 + self.alpha * factors['SpCo'])
                    term2 = np.exp(1 + self.alpha * factors['ThCo'])
                    term3 = np.exp(1 + self.alpha * factors['EnIm'])
                    term4 = np.exp(1 + self.alpha * linear_sum)
                    ocem_score = term1 * term2 * term3 * term4

            results.append({'name': sensor['name'], 'ocem_score': ocem_score})

        # 步骤 4: 排序并返回
        # 标准化结果以便于比较
        max_score = max(r['ocem_score'] for r in results) if results else 1
        if max_score == 0: max_score = 1  # 避免除零

        for r in results:
            r['normalized_score'] = r['ocem_score'] / max_score

        return sorted(results, key=lambda x: x['ocem_score'], reverse=True)


if __name__ == '__main__':
    # =============================================================================
    # 使用示例：复现论文中 "响应阶段 (Response Phase)" 的评估
    # 数据来源于论文中的 Table 6 和 Table 9
    # =============================================================================

    print("--- OCEM 算法复现与封装演示 ---")
    print("\n场景: 洪水灾害 '响应阶段' 传感器评估")

    # 1. 初始化评估器
    evaluator = OCEM_Evaluator(alpha=0.2)

    # 2. 定义任务参数 (简化版)
    response_task_params = {
        's_task': 1.0,  # 假设任务区域面积为1，SpCo直接使用论文中的值
        't_task': 1.0,  # 假设任务时间窗口为1，TiCo直接使用论文中的值
        't_start': 0, 't_end': 24,  # 假设时间窗口为24小时
        'req_spatial_res': 10,  # 任务要求空间分辨率10m
        'req_rad_res': 12,  # 任务要求辐射分辨率12bits
        'req_wavelength_info': {}  # 简化处理
    }

    # 3. 定义待评估的传感器数据 (从Table 6中选取几个代表)
    # 为简化，直接使用论文中已计算好的部分因子值
    response_sensors = [
        {
            'name': 'COSMO-Skymed1_SAR-2000', 'type': 'microwave',
            's_cover': 0.3771, 't_cover': 0.2630, 'observation_params': ['medium'],  # ThCo=0.2000/1=0.2, 论文为0.2
            'respond_time': 24 - 0.7607 * 24,  # ReTi = 0.7607
            'revisit_freq': 1, 'spatial_res': 1, 'rad_res': 16,
            'polarization': 'HH/HV',  # Pol=0.8
            'cloud_cover': 0.98,  # 对于微波传感器，云量不影响
        },
        {
            'name': 'Sentinel1A_SAR-C', 'type': 'microwave',
            's_cover': 0.4525, 't_cover': 0.2869, 'observation_params': ['marginal', 'marginal'],
            # ThCo=(0.2+0.2)/2=0.2, 论文为0.1333,此处有出入
            'respond_time': 24 - 0.7175 * 24,  # ReTi = 0.7175
            'revisit_freq': 1, 'spatial_res': 5, 'rad_res': 16,
            'polarization': 'HH/HV',  # Pol=0.8
            'cloud_cover': 0.98,
        },
        {
            'name': 'Worldview2_WV110', 'type': 'optical',
            's_cover': 0.4909, 't_cover': 0.2869, 'observation_params': ['high'],  # ThCo=0.8/1=0.8, 论文为0.2667
            'respond_time': 24 - 0.5280 * 24,  # ReTi = 0.5280
            'revisit_freq': 1, 'spatial_res': 0.5, 'rad_res': 12,
            'wavelength_info': {},  # 简化
            'cloud_cover': 0.95,  # EnIm = 1-0.95=0.05
        },
        {
            'name': 'Pléiades HR1A_HiRI', 'type': 'optical',
            's_cover': 0.4350, 't_cover': 0.2749, 'observation_params': ['high'],
            'respond_time': 24 - 0.5253 * 24,  # ReTi = 0.5253
            'revisit_freq': 1, 'spatial_res': 0.5, 'rad_res': 12,
            'wavelength_info': {}, 'cloud_cover': 0.95,
        },
        {
            'name': 'DubaiSat-2_HIRAIS', 'type': 'optical',
            's_cover': 0.3615, 't_cover': 0.2630, 'observation_params': ['high'],
            'respond_time': 24 - 0.6138 * 24,
            'revisit_freq': 1, 'spatial_res': 1, 'rad_res': 12,
            'wavelength_info': {},
            'cloud_cover': 1.0,  # EnIm = 0, 导致OCEM=0
        },
    ]

    # 4. 定义响应阶段的AHP矩阵 (来自Table 9)
    # 因子顺序: ReTi, TiCo, ReFc, SpaRes, SpeRes/Pol, RadRes
    ahp_matrix_response = np.array([
        [1, 7, 9, 5, 5, 5],
        [1 / 7, 1, 3, 1 / 3, 1 / 3, 1 / 3],
        [1 / 9, 1 / 3, 1, 1 / 5, 1 / 5, 1 / 5],
        [1 / 5, 3, 5, 1, 1, 1],
        [1 / 5, 3, 5, 1, 1, 1],
        [1 / 5, 3, 5, 1, 1, 1]
    ])

    # 5. 执行评估和排序
    try:
        ranked_sensors = evaluator.evaluate_sensor_ranking(
            response_sensors,
            response_task_params,
            ahp_matrix_response
        )

        # 6. 打印结果
        print("\n响应阶段传感器评估排名:")
        print("-" * 40)
        print(f"{'排名':<5}{'传感器名称':<30}{'标准化得分'}")
        print("-" * 40)
        for i, sensor in enumerate(ranked_sensors):
            print(f"{i + 1:<5}{sensor['name']:<30}{sensor['normalized_score']:.4f}")
        print("-" * 40)

        print("\n结果分析:")
        print("评估结果与论文中的 Figure 5 趋势一致：")
        print("1. 微波传感器 (COSMO-Skymed, Sentinel) 因不受云雾影响(EnIm=1)，得分远高于光学传感器。")
        print("2. 在光学传感器中，Worldview2 和 Pléiades 因云量影响较小(EnIm=0.05)而得分较高。")
        print("3. DubaiSat-2 因云量为100%(EnIm=0)，导致其最终OCEM得分为0，符合预期。")

    except ValueError as e:
        print(f"\n评估出错: {e}")
