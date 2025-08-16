# -*- coding: utf-8 -*-
"""
PROJECT_NAME: Other_Python
FILE_NAME: SSCI
AUTHOR: welt
E_MAIL: tjlwelt@foxmail.com
DATE: 2025-08-11
"""

import numpy as np
from sklearn.decomposition import PCA


class SSCI_Evaluator:
	"""
	根据论文 "Spaceborne Earth-Observing Optical Sensor Static Capability Index
	for Clustering" (Chen et al., 2015) 复现并封装SSCI计算算法。

	该类实现了以下核心功能:
	1. 传感器静态能力参数的预处理（倒数转换、标准化、加权）[cite: 1085]。
	2. 应用主成分分析（PCA）提取关键能力成分 [cite: 1125]。
	3. 计算每个传感器的最终静态能力指数（SSCI）[cite: 1136]。

	使用方法:
	1. 创建 `SSCI_Evaluator` 实例。
	2. 准备原始数据（一个NumPy数组，行代表传感器，列代表参数）。
	3. 定义需要取倒数的参数列索引和各项参数的权重。
	4. 调用 `calculate_ssci` 方法，该方法将返回每个传感器的SSCI分数
	   以及用于后续聚类的“能力得分向量” 。
	"""

	def preprocess_data(self,
	                    raw_data: np.ndarray,
	                    reciprocal_cols: list = [],
	                    weights: np.ndarray = None) -> np.ndarray:
		"""
		对原始静态能力参数矩阵进行预处理。
		流程依据论文 Section II-A 和 II-B。

		Args:
			raw_data (np.ndarray): 原始数据矩阵 (n_sensors, n_parameters)。
			reciprocal_cols (list): 需要取倒数的列索引列表 [cite: 1091]。
									适用于值越小能力越强的参数。
			weights (np.ndarray): 施加于各参数的权重向量 (1, n_parameters) [cite: 1097, 1098]。
								  若为None，则不进行加权。

		Returns:
			np.ndarray: 经过预处理（倒数、标准化、加权）后的数据矩阵。
		"""
		processed_data = raw_data.astype(float)

		# 步骤 1: 对指定列取倒数 [cite: 1091]
		for col_idx in reciprocal_cols:
			# 防止除以零
			processed_data[:, col_idx] = np.reciprocal(processed_data[:, col_idx],
			                                           where=processed_data[:, col_idx] != 0)

		# 步骤 2: 标准化 - 除以每列的最大值
		max_vals = np.max(processed_data, axis=0)
		# 防止除以零
		processed_data = np.divide(processed_data, max_vals, where=max_vals != 0)

		# 步骤 3: 人为加权 - 乘以用户定义的权重 [cite: 1107, 1111]
		if weights is not None:
			if weights.shape[0] != processed_data.shape[1]:
				raise ValueError("权重数量必须与参数数量匹配。")
			processed_data = processed_data * weights

		return processed_data

	def calculate_ssci(self,
	                   raw_data: np.ndarray,
	                   reciprocal_cols: list,
	                   weights: np.ndarray,
	                   info_threshold: float = 0.90) -> tuple:
		"""
		计算SSCI并返回能力得分向量。
		流程依据论文 Section II-C 和 II-D。

		Args:
			raw_data (np.ndarray): 原始数据矩阵 (n_sensors, n_parameters)。
			reciprocal_cols (list): 需要取倒数的列索引。
			weights (np.ndarray): 参数的权重向量。
			info_threshold (float): PCA保留信息量的阈值 (例如0.9代表保留90%的方差) 。

		Returns:
			tuple: 包含两部分的元组:
				- ssci_scores (np.ndarray): 每个传感器的SSCI分数的一维数组 [cite: 1136]。
				- capability_vectors (np.ndarray): 每个传感器的“能力得分向量”，
				  可用于后续的SOM聚类 [cite: 1134, 1184]。
		"""
		# 1. 预处理数据
		preprocessed_matrix = self.preprocess_data(raw_data, reciprocal_cols, weights)

		# 2. 执行PCA
		pca = PCA()
		# principal_components 即论文中的 "capability score vector"
		capability_vectors = pca.fit_transform(preprocessed_matrix)

		# 3. 确定要保留的主成分数量
		explained_variance_ratio = pca.explained_variance_ratio_
		cumulative_variance = np.cumsum(explained_variance_ratio)
		n_components = np.argmax(cumulative_variance >= info_threshold) + 1

		# 截取所需的主成分得分和方差解释率
		capability_vectors_selected = capability_vectors[:, :n_components]
		explained_variance_ratio_selected = explained_variance_ratio[:n_components]

		# 4. 计算SSCI
		# SSCI是主成分得分的加权和，权重是每个主成分的方差贡献率 [cite: 1136, 1142]
		ssci_weights = explained_variance_ratio_selected / np.sum(explained_variance_ratio_selected)
		ssci_scores = np.sum(capability_vectors_selected * ssci_weights, axis=1)

		return ssci_scores, capability_vectors_selected


if __name__ == '__main__':
	print("--- SSCI 算法复现与封装演示 ---")

	# 1. 初始化评估器
	evaluator = SSCI_Evaluator()

	# 2. 创建模拟数据
	# 假设我们有10个传感器和6个静态能力参数
	# 参数顺序: 空间分辨率(m), 视场角(deg), 信噪比(SNR), 波段数, 数据速率(Mbps), 设计寿命(yrs)
	sensor_names = [f"Sensor-{chr(65 + i)}" for i in range(10)]
	mock_raw_data = np.array([
		# Res(m), FOV(deg), SNR, Bands, Rate(Mbps), Life(yrs)
		[0.5, 1.2, 150, 8, 800, 7],  # 高分敏捷型
		[0.8, 1.0, 120, 4, 600, 7],  # 高分敏捷型
		[1.0, 2.5, 100, 8, 500, 5],  # 中高分型
		[2.5, 5.0, 90, 12, 400, 5],  # 中分高光谱型
		[5.0, 15.0, 80, 7, 300, 10],  # 中分宽幅型
		[4.0, 18.0, 85, 7, 350, 10],  # 中分宽幅型
		[15.0, 60.0, 200, 6, 100, 15],  # 低分超宽幅型
		[30.0, 80.0, 250, 6, 50, 15],  # 低分超宽幅型
		[0.7, 0.9, 200, 1, 900, 5],  # 高分全色型
		[10.0, 45.0, 180, 5, 200, 12]  # 低分宽幅型
	])

	# 3. 定义预处理参数
	# 空间分辨率(索引0)值越小越好，需要取倒数 [cite: 1090, 1091]
	reciprocal_columns = [0]

	# 假设任务为"灾害监测阶段" (Disaster Monitoring), 需要高分辨率。权重依据 Table V [cite: 1301]
	# 权重顺序对应6个参数: Res, FOV, SNR, Bands, Rate, Life
	task_weights = np.array([9, 3, 5, 1, 2, 2])
	print(f"\n当前任务权重 (灾害监测): {task_weights} [cite: 1301]")

	# 4. 执行SSCI计算
	try:
		ssci_results, cap_vectors = evaluator.calculate_ssci(
			raw_data=mock_raw_data,
			reciprocal_cols=reciprocal_columns,
			weights=task_weights,
			info_threshold=0.95  # 设置保留95%的信息
		)

		# 5. 打印结果
		print("\n--- SSCI 计算结果 ---")
		sorted_indices = np.argsort(ssci_results)[::-1]  # 降序排序
		print(f"{'排名':<5}{'传感器名称':<15}{'SSCI 得分':<15}")
		print("-" * 40)
		for rank, idx in enumerate(sorted_indices):
			print(f"{rank + 1:<5}{sensor_names[idx]:<15}{ssci_results[idx]:<15.4f}")

		print("\n--- 后续聚类步骤说明 ---")
		print("SSCI的计算过程产出了每个传感器的“能力得分向量” [cite: 1134]。")
		print(f"此示例中，能力得分向量的维度为: {cap_vectors.shape[1]}")
		print("根据论文 Section III 的描述，这些向量将作为自组织映射（SOM）神经网络的输入，\n"
		      "以实现对传感器的无监督聚类 [cite: 1179, 1184]。")
		print("通过这种方式，可以将静态能力相似的传感器自动地划分到同一组中 [cite: 1430]，\n"
		      "为后续更精细的动态能力评估（如DOCI）提供科学的候选集 [cite: 966, 1431]。")

	except Exception as e:
		print(f"计算过程中出现错误: {e}")
