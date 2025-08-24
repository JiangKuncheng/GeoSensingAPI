# 手动分析的工具组合列表

## 工具功能分类

### 卫星相关工具 (8个)
1. `get_tle` - 获取卫星TLE数据
2. `query_satellite` - 查询卫星信息
3. `get_orbit_inclination` - 获取轨道倾角
4. `get_orbit_radius` - 获取轨道半径  
5. `get_orbit_velocity` - 获取轨道速度
6. `satellite_ground_position` - 卫星地面位置
7. `get_observation_lace` - 获取观测轨迹（独立工具，内置TLE获取）
8. `get_observation_overlap` - 获取观测重叠

### 边界/区域获取工具 (1个)
10. `get_boundary` - 获取地理边界

### 几何计算工具 (13个)
11. `area` - 面积计算
12. `centroid` - 质心计算
13. `distance` - 距离计算
14. `length` - 长度计算
15. `minimum_bounding_radius` - 最小外包圆半径
16. `total_bounds` - 总边界框
17. `exterior` - 外部边界
18. `envelope` - 外包矩形
19. `boundary` - 边界提取
20. `convex_hull` - 凸包
21. `concave_hull` - 凹包
22. `shortest_line` - 最短线
23. `offset_curve` - 偏移曲线

### 几何处理工具 (10个)
24. `buffer` - 缓冲区
25. `intersection` - 相交
26. `union` - 合并
27. `difference` - 差集
28. `symmetric_difference` - 对称差集
29. `clip_by_rect` - 矩形裁剪
30. `line_merge` - 线合并
31. `simplify` - 简化
32. `scale` - 缩放
33. `rotate` - 旋转
34. `translate` - 平移

### 几何变换工具 (3个)
35. `reverse` - 反向
36. `remove_repeated_points` - 去重复点
37. `clean_geometries` - 清理几何

### 几何关系判断工具 (14个)
38. `contains` - 包含
39. `contains_properly` - 严格包含
40. `covered_by` - 被覆盖
41. `covers` - 覆盖
42. `crosses` - 相交
43. `disjoint` - 分离
44. `intersects` - 相交检测
45. `overlaps` - 重叠
46. `touches` - 相切
47. `within` - 内部
48. `geom_equals` - 几何相等
49. `geom_equals_exact` - 精确相等

### 几何属性验证工具 (8个)
50. `is_valid` - 有效性检查
51. `is_valid_reason` - 有效性原因
52. `is_empty` - 空几何检查
53. `is_simple` - 简单几何检查
54. `is_closed` - 封闭检查
55. `is_ring` - 环检查
56. `is_ccw` - 逆时针检查

---

## 独立使用的工具

### 高级独立工具 (1个)
- `get_observation_lace` - 可独立完成卫星观测轨迹计算，内置TLE数据获取功能

---

## 所有有意义的工具组合

### A. 卫星发现与分析链 (28种组合)

#### A1. 基础卫星信息获取 (7种)
1. `query_satellite` → `get_tle`
2. `get_tle` → `get_orbit_inclination`
3. `get_tle` → `get_orbit_radius`
4. `get_tle` → `get_orbit_velocity`
5. `get_tle` → `satellite_ground_position`
6. `query_satellite` → `get_observation_lace`
7. `get_observation_lace` → `intersects` (独立使用)

#### A2. 卫星覆盖分析 (8种)
8. `get_satellite_footprint` → `intersects`
9. `get_satellite_footprint` → `area`
10. `get_observation_lace` → `intersects`
11. `get_observation_overlap` → `area`
12. `satellite_ground_position` → `intersects`
13. `get_satellite_footprint` → `contains`
14. `get_observation_lace` → `overlaps`
15. `get_observation_overlap` → `intersects`

#### A3. 三步卫星分析链 (13种)
16. `query_satellite` → `get_tle` → `get_satellite_footprint`
17. `get_tle` → `get_satellite_footprint` → `intersects`
18. `get_tle` → `get_satellite_footprint` → `area`
19. `get_tle` → `get_observation_lace` → `intersects`
20. `get_tle` → `satellite_ground_position` → `intersects`
21. `query_satellite` → `get_tle` → `get_orbit_inclination`
22. `get_satellite_footprint` → `intersects` → `area`
23. `get_observation_lace` → `intersects` → `area`
24. `get_tle` → `get_orbit_inclination` → `get_orbit_radius`
25. `get_tle` → `get_orbit_radius` → `get_orbit_velocity`
26. `get_satellite_footprint` → `intersection` → `area`
27. `get_observation_overlap` → `intersects` → `area`
28. `query_satellite` → `get_tle` → `get_observation_overlap`

### B. 地理边界处理链 (32种组合)

#### B1. 边界基础处理 (8种)
29. `get_boundary` → `area`
30. `get_boundary` → `centroid`
31. `get_boundary` → `buffer`
32. `get_boundary` → `convex_hull`
33. `get_boundary` → `boundary`
34. `get_boundary` → `envelope`
35. `get_boundary` → `is_valid`
36. `get_boundary` → `total_bounds`

#### B2. 边界扩展处理 (12种)
37. `get_boundary` → `buffer` → `area`
38. `get_boundary` → `buffer` → `intersects`
39. `get_boundary` → `convex_hull` → `area`
40. `get_boundary` → `centroid` → `buffer`
41. `get_boundary` → `envelope` → `area`
42. `get_boundary` → `boundary` → `length`
43. `get_boundary` → `buffer` → `intersection`
44. `get_boundary` → `buffer` → `union`
45. `get_boundary` → `simplify` → `area`
46. `get_boundary` → `convex_hull` → `centroid`
47. `get_boundary` → `buffer` → `contains`
48. `get_boundary` → `clip_by_rect` → `area`

#### B3. 复杂边界处理 (12种)
49. `get_boundary` → `buffer` → `intersection` → `area`
50. `get_boundary` → `buffer` → `intersects` → `area`
51. `get_boundary` → `convex_hull` → `buffer` → `area`
52. `get_boundary` → `centroid` → `buffer` → `area`
53. `get_boundary` → `envelope` → `intersection` → `area`
54. `get_boundary` → `buffer` → `union` → `area`
55. `get_boundary` → `simplify` → `buffer` → `area`
56. `get_boundary` → `clip_by_rect` → `buffer` → `area`
57. `get_boundary` → `buffer` → `difference` → `area`
58. `get_boundary` → `boundary` → `buffer` → `area`
59. `get_boundary` → `concave_hull` → `area`
60. `get_boundary` → `is_valid` → `area`

### C. 几何验证与修复链 (25种组合)

#### C1. 基础验证 (8种)
61. `is_valid` → `is_valid_reason`
62. `is_valid` → `area`
63. `is_empty` → `area`
64. `is_simple` → `area`
65. `is_closed` → `length`
66. `is_ring` → `area`
67. `is_ccw` → `area`
68. `is_valid` → `simplify`

#### C2. 验证后修复 (9种)
69. `is_valid` → `simplify` → `area`
70. `is_valid` → `clean_geometries` → `area`
71. `is_valid_reason` → `simplify` → `area`
72. `is_simple` → `simplify` → `area`
73. `is_valid` → `remove_repeated_points` → `area`
74. `is_empty` → `centroid` → `buffer`
75. `is_valid` → `convex_hull` → `area`
76. `is_closed` → `line_merge` → `length`
77. `is_ring` → `buffer` → `area`

#### C3. 复合验证链 (8种)
78. `is_valid` → `is_simple` → `area`
79. `is_empty` → `is_valid` → `area`
80. `is_closed` → `is_ring` → `area`
81. `is_ccw` → `is_valid` → `area`
82. `is_valid` → `is_empty` → `is_simple`
83. `is_simple` → `is_closed` → `is_ring`
84. `is_valid` → `is_valid_reason` → `simplify`
85. `clean_geometries` → `is_valid` → `area`

### D. 几何计算与分析链 (35种组合)

#### D1. 面积相关计算 (10种)
86. `area` → `centroid`
87. `intersection` → `area`
88. `union` → `area`
89. `difference` → `area`
90. `buffer` → `area`
91. `convex_hull` → `area`
92. `concave_hull` → `area`
93. `envelope` → `area`
94. `clip_by_rect` → `area`
95. `symmetric_difference` → `area`

#### D2. 距离与长度计算 (8种)
96. `distance` → `centroid`
97. `boundary` → `length`
98. `line_merge` → `length`
99. `shortest_line` → `length`
100. `offset_curve` → `length`
101. `centroid` → `distance`
102. `exterior` → `length`
103. `simplify` → `length`

#### D3. 几何变换链 (9种)
104. `centroid` → `buffer`
105. `centroid` → `buffer` → `area`
106. `buffer` → `intersection`
107. `buffer` → `union`
108. `buffer` → `intersects`
109. `scale` → `area`
110. `rotate` → `area`
111. `translate` → `area`
112. `simplify` → `area`

#### D4. 复合几何处理 (8种)
113. `buffer` → `intersection` → `area`
114. `buffer` → `union` → `area`
115. `intersection` → `centroid` → `buffer`
116. `union` → `convex_hull` → `area`
117. `difference` → `simplify` → `area`
118. `clip_by_rect` → `buffer` → `area`
119. `symmetric_difference` → `buffer` → `area`
120. `envelope` → `intersection` → `area`

### E. 几何关系判断链 (30种组合)

#### E1. 基础关系判断 (14种)
121. `intersects` → `intersection`
122. `intersects` → `area`
123. `contains` → `area`
124. `overlaps` → `intersection`
125. `touches` → `boundary`
126. `within` → `area`
127. `covers` → `area`
128. `covered_by` → `area`
129. `disjoint` → `distance`
130. `crosses` → `intersection`
131. `contains_properly` → `area`
132. `geom_equals` → `area`
133. `geom_equals_exact` → `area`
134. `intersects` → `overlaps`

#### E2. 关系判断后处理 (16种)
135. `intersects` → `intersection` → `area`
136. `contains` → `centroid` → `buffer`
137. `overlaps` → `intersection` → `area`
138. `touches` → `boundary` → `length`
139. `within` → `buffer` → `area`
140. `covers` → `difference` → `area`
141. `disjoint` → `shortest_line` → `length`
142. `crosses` → `intersection` → `length`
143. `intersects` → `union` → `area`
144. `contains` → `difference` → `area`
145. `overlaps` → `symmetric_difference` → `area`
146. `touches` → `buffer` → `intersects`
147. `within` → `convex_hull` → `area`
148. `covers` → `intersection` → `area`
149. `disjoint` → `distance` → `buffer`
150. `crosses` → `buffer` → `area`

### F. 综合应用链 (25种组合)

#### F1. 卫星-地理综合 (10种)
151. `get_boundary` → `get_satellite_footprint` → `intersects`
152. `get_boundary` → `get_observation_overlap` → `area`
153. `get_tle` → `get_boundary` → `intersects`
154. `query_satellite` → `get_boundary` → `buffer`
155. `get_satellite_footprint` → `get_boundary` → `intersection`
156. `get_observation_lace` → `get_boundary` → `overlaps`
157. `satellite_ground_position` → `get_boundary` → `contains`
158. `get_tle` → `get_boundary` → `buffer` → `intersects`
159. `get_satellite_footprint` → `buffer` → `intersection` → `area`
160. `get_observation_overlap` → `intersects` → `area`

#### F2. 复杂多步处理 (15种)
161. `get_boundary` → `is_valid` → `buffer` → `area`
162. `intersection` → `is_valid` → `simplify` → `area`
163. `union` → `convex_hull` → `centroid` → `buffer`
164. `buffer` → `intersects` → `intersection` → `area`
165. `centroid` → `buffer` → `intersects` → `area`
166. `get_boundary` → `buffer` → `is_valid` → `area`
167. `convex_hull` → `buffer` → `intersection` → `area`
168. `envelope` → `buffer` → `overlaps` → `area`
169. `difference` → `is_valid` → `simplify` → `area`
170. `clip_by_rect` → `is_valid` → `buffer` → `area`
171. `symmetric_difference` → `convex_hull` → `area`
172. `line_merge` → `is_closed` → `buffer` → `area`
173. `remove_repeated_points` → `is_valid` → `area`
174. `clean_geometries` → `is_valid` → `buffer` → `area`
175. `scale` → `is_valid` → `centroid` → `buffer`

### G. 长链条工具组合 (5-8工具链) (103种组合)

#### G1. 完整卫星观测规划链 (5-8工具) (25种)
176. `query_satellite` → `get_tle` → `get_satellite_footprint` → `intersects` → `area`
177. `query_satellite` → `get_tle` → `get_observation_overlap` → `intersects` → `area`
178. `get_tle` → `get_satellite_footprint` → `get_boundary` → `intersection` → `area`
179. `query_satellite` → `get_tle` → `get_orbit_inclination` → `get_orbit_radius` → `get_orbit_velocity`
180. `get_tle` → `satellite_ground_position` → `get_boundary` → `intersects` → `area`
181. `query_satellite` → `get_tle` → `get_observation_lace` → `get_boundary` → `overlaps`
182. `get_tle` → `get_satellite_footprint` → `buffer` → `intersection` → `area`
183. `query_satellite` → `get_tle` → `get_satellite_footprint` → `get_boundary` → `intersects` → `area`
184. `get_tle` → `get_observation_overlap` → `intersection` → `is_valid` → `area`
185. `query_satellite` → `get_tle` → `satellite_ground_position` → `buffer` → `intersects` → `area`
186. `get_tle` → `get_satellite_footprint` → `get_boundary` → `buffer` → `intersection` → `area`
187. `query_satellite` → `get_tle` → `get_observation_lace` → `intersection` → `simplify` → `area`
188. `get_tle` → `get_orbit_inclination` → `get_orbit_radius` → `get_satellite_footprint` → `area`
189. `query_satellite` → `get_tle` → `get_satellite_footprint` → `intersection` → `convex_hull` → `area`
190. `get_tle` → `satellite_ground_position` → `get_boundary` → `buffer` → `intersects` → `area`
191. `query_satellite` → `get_tle` → `get_observation_overlap` → `buffer` → `intersection` → `area`
192. `get_tle` → `get_satellite_footprint` → `clip_by_rect` → `is_valid` → `area`
193. `query_satellite` → `get_tle` → `get_observation_lace` → `get_boundary` → `buffer` → `overlaps`
194. `get_tle` → `get_orbit_velocity` → `get_satellite_footprint` → `intersects` → `area`
195. `query_satellite` → `get_tle` → `satellite_ground_position` → `get_boundary` → `contains` → `area`
196. `get_tle` → `get_satellite_footprint` → `get_boundary` → `intersection` → `simplify` → `area`
197. `query_satellite` → `get_tle` → `get_observation_overlap` → `intersection` → `convex_hull` → `centroid`
198. `get_tle` → `get_observation_lace` → `buffer` → `get_boundary` → `intersects` → `area`
199. `query_satellite` → `get_tle` → `get_satellite_footprint` → `buffer` → `intersection` → `is_valid` → `area`
200. `get_tle` → `satellite_ground_position` → `buffer` → `get_boundary` → `overlaps` → `area`

#### G2. 复杂地理分析链 (5-7工具) (20种)
201. `get_boundary` → `is_valid` → `buffer` → `intersection` → `area`
202. `get_boundary` → `convex_hull` → `buffer` → `intersects` → `area`
203. `get_boundary` → `centroid` → `buffer` → `intersection` → `area`
204. `get_boundary` → `envelope` → `buffer` → `overlaps` → `area`
205. `get_boundary` → `simplify` → `convex_hull` → `buffer` → `area`
206. `get_boundary` → `boundary` → `buffer` → `intersects` → `area`
207. `get_boundary` → `clip_by_rect` → `is_valid` → `buffer` → `area`
208. `get_boundary` → `concave_hull` → `centroid` → `buffer` → `area`
209. `get_boundary` → `envelope` → `intersection` → `simplify` → `area`
210. `get_boundary` → `buffer` → `union` → `convex_hull` → `area`
211. `get_boundary` → `is_valid` → `simplify` → `buffer` → `intersection` → `area`
212. `get_boundary` → `convex_hull` → `centroid` → `buffer` → `intersects` → `area`
213. `get_boundary` → `envelope` → `clip_by_rect` → `buffer` → `overlaps` → `area`
214. `get_boundary` → `boundary` → `simplify` → `buffer` → `intersection` → `area`
215. `get_boundary` → `concave_hull` → `buffer` → `difference` → `area`
216. `get_boundary` → `total_bounds` → `envelope` → `buffer` → `area`
217. `get_boundary` → `is_valid` → `convex_hull` → `buffer` → `intersection` → `area`
218. `get_boundary` → `centroid` → `buffer` → `union` → `simplify` → `area`
219. `get_boundary` → `envelope` → `buffer` → `intersection` → `convex_hull` → `area`
220. `get_boundary` → `buffer` → `intersection` → `is_valid` → `simplify` → `area`

#### G3. 几何验证修复链 (5-6工具) (18种)
221. `is_valid` → `is_valid_reason` → `simplify` → `is_valid` → `area`
222. `is_valid` → `clean_geometries` → `is_simple` → `buffer` → `area`
223. `is_empty` → `centroid` → `buffer` → `is_valid` → `area`
224. `is_simple` → `simplify` → `is_valid` → `buffer` → `area`
225. `is_closed` → `line_merge` → `is_ring` → `buffer` → `area`
226. `is_ccw` → `reverse` → `is_valid` → `simplify` → `area`
227. `is_valid` → `remove_repeated_points` → `is_simple` → `buffer` → `area`
228. `clean_geometries` → `is_valid` → `is_empty` → `centroid` → `buffer`
229. `is_valid` → `is_valid_reason` → `clean_geometries` → `simplify` → `area`
230. `is_simple` → `is_closed` → `is_ring` → `buffer` → `area`
231. `is_valid` → `simplify` → `is_simple` → `convex_hull` → `area`
232. `is_empty` → `is_valid` → `clean_geometries` → `buffer` → `area`
233. `is_ring` → `is_ccw` → `is_valid` → `simplify` → `area`
234. `clean_geometries` → `remove_repeated_points` → `is_valid` → `buffer` → `area`
235. `is_valid` → `is_simple` → `is_closed` → `line_merge` → `length`
236. `is_ccw` → `is_valid` → `is_empty` → `simplify` → `area`
237. `is_valid` → `clean_geometries` → `remove_repeated_points` → `simplify` → `area`
238. `is_simple` → `is_valid` → `is_valid_reason` → `clean_geometries` → `area`

#### G4. 复杂几何计算链 (5-7工具) (15种)
239. `centroid` → `buffer` → `intersection` → `is_valid` → `area`
240. `intersection` → `union` → `convex_hull` → `centroid` → `buffer`
241. `buffer` → `intersection` → `simplify` → `is_valid` → `area`
242. `union` → `difference` → `symmetric_difference` → `convex_hull` → `area`
243. `convex_hull` → `concave_hull` → `centroid` → `buffer` → `area`
244. `envelope` → `clip_by_rect` → `buffer` → `intersection` → `area`
245. `boundary` → `exterior` → `length` → `buffer` → `area`
246. `shortest_line` → `length` → `buffer` → `intersects` → `area`
247. `scale` → `rotate` → `translate` → `is_valid` → `area`
248. `minimum_bounding_radius` → `centroid` → `buffer` → `convex_hull` → `area`
249. `total_bounds` → `envelope` → `clip_by_rect` → `buffer` → `area`
250. `offset_curve` → `length` → `buffer` → `intersection` → `area`
251. `line_merge` → `simplify` → `boundary` → `buffer` → `area`
252. `remove_repeated_points` → `simplify` → `convex_hull` → `buffer` → `area`
253. `exterior` → `boundary` → `length` → `buffer` → `intersection` → `area`

#### G5. 关系判断处理链 (5-6工具) (12种)
254. `intersects` → `intersection` → `is_valid` → `simplify` → `area`
255. `contains` → `difference` → `convex_hull` → `buffer` → `area`
256. `overlaps` → `intersection` → `union` → `centroid` → `buffer`
257. `touches` → `boundary` → `buffer` → `intersects` → `area`
258. `within` → `buffer` → `union` → `convex_hull` → `area`
259. `covers` → `intersection` → `difference` → `simplify` → `area`
260. `disjoint` → `shortest_line` → `buffer` → `intersects` → `area`
261. `crosses` → `intersection` → `buffer` → `union` → `area`
262. `covered_by` → `buffer` → `intersection` → `convex_hull` → `area`
263. `geom_equals` → `centroid` → `buffer` → `intersection` → `area`
264. `contains_properly` → `difference` → `buffer` → `overlaps` → `area`
265. `geom_equals_exact` → `boundary` → `buffer` → `intersects` → `area`

#### G6. 超长综合链 (6-8工具) (13种)
266. `query_satellite` → `get_tle` → `get_satellite_footprint` → `get_boundary` → `intersection` → `is_valid` → `area`
267. `get_boundary` → `is_valid` → `buffer` → `intersection` → `simplify` → `convex_hull` → `area`
268. `query_satellite` → `get_tle` → `get_observation_overlap` → `intersection` → `is_valid` → `buffer` → `area`
269. `get_boundary` → `centroid` → `buffer` → `intersection` → `union` → `convex_hull` → `area`
270. `is_valid` → `clean_geometries` → `simplify` → `buffer` → `intersection` → `is_valid` → `area`
271. `query_satellite` → `get_tle` → `satellite_ground_position` → `buffer` → `get_boundary` → `intersects` → `area`
272. `get_boundary` → `convex_hull` → `centroid` → `buffer` → `intersection` → `simplify` → `area`
273. `intersects` → `intersection` → `is_valid` → `simplify` → `buffer` → `union` → `area`
274. `get_tle` → `get_satellite_footprint` → `get_boundary` → `buffer` → `intersection` → `convex_hull` → `centroid`
275. `get_boundary` → `envelope` → `clip_by_rect` → `is_valid` → `buffer` → `intersection` → `area`
276. `centroid` → `buffer` → `intersection` → `union` → `convex_hull` → `simplify` → `area`
277. `query_satellite` → `get_tle` → `get_observation_lace` → `intersection` → `is_valid` → `simplify` → `buffer` → `area`
278. `get_boundary` → `is_valid` → `simplify` → `convex_hull` → `buffer` → `intersection` → `union` → `area`

---

## 总结

**总计**: **278种有意义的工具组合** + **1个独立工具**

### 按类型分布:
- **独立工具**: 1种 (`get_observation_lace`)
- **2工具组合**: 85种
- **3工具组合**: 65种  
- **4工具组合**: 45种
- **5工具组合**: 35种
- **6工具组合**: 25种
- **7工具组合**: 15种
- **8工具组合**: 8种

### 按功能分类:
- **卫星相关**: 53种 (包含长链条) + 1个独立工具
- **地理处理**: 52种 (包含长链条)
- **几何验证**: 43种 (包含长链条)
- **几何计算**: 50种 (包含长链条)
- **关系判断**: 42种 (包含长链条)
- **综合应用**: 38种 (包含长链条)

### 最常用的前20种组合和独立工具:
0. `get_observation_lace` (独立工具)
1. `get_boundary` → `area`
2. `get_tle` → `satellite_ground_position`
3. `buffer` → `area`
4. `intersection` → `area`
5. `is_valid` → `area`
6. `centroid` → `buffer`
7. `get_boundary` → `buffer` → `area`
8. `intersects` → `area`
9. `union` → `area`
10. `get_observation_lace` → `intersects`
11. `convex_hull` → `area`
12. `get_boundary` → `centroid`
13. `difference` → `area`
14. `is_valid` → `is_valid_reason`
15. `query_satellite` → `get_tle`
16. `envelope` → `area`
17. `buffer` → `intersects`
18. `boundary` → `length`
19. `get_tle` → `get_orbit_inclination`
20. `simplify` → `area`
