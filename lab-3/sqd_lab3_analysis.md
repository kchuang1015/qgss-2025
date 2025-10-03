# 專案分析報告：量子化學模擬的 SQD 實作

感謝您提供程式碼庫。以下是根據提供的內容，對此專案的全面分析。此專案似乎是一個單一的 Jupyter notebook 檔案，專注於 **Sample-based Quantum Diagonalization (SQD)** 的教學，該演算法使用 Qiskit 和 PySCF 來估計分子的基態能量。notebook 示範了模擬 N₂ 分子的流程，包括 ansatz 建構、量子電路執行，以及使用配置恢復的後處理。我將依據指南的結構進行報告：概述、相關類型定義/介面、關鍵實作，以及依賴關係。所有引用均指向 notebook 內容（視為單一檔案：`sqd_notebook.ipynb`，行號基於提供的文字近似）。

## 1. 相關文件洞見概述
此專案是一個自成一體的 Jupyter notebook 教學檔案，標題為「SQD Implementation for Quantum Chemistry Simulations」。它同時作為文件和可執行程式碼，逐步解釋 SQD 演算法。關鍵洞見來自 notebook：

- **目的**：notebook 教導如何應用 SQD 來近似估計平衡狀態下分子的基態能量，使用 6-31G 基組。它涵蓋將經典分子資料映射到量子問題、電路最佳化、在 IBM Quantum 後端（例如 `ibm_brisbane`、`ibm_torino`）執行，以及透過自一致迭代進行後處理（行 ~100-500）。
- **工作流程結構**（notebook 中的順序區段）：
  - **SQD 介紹**：解釋演機動機，包括配置恢復和小空間對角化（行 ~100-500）。
  - **步驟 1：映射到量子問題**（行 ~500-800）：使用 PySCF 建構分子漢米爾頓量，並使用 ffsim 建構 LUCJ（Local Unitary Coupled-cluster Jastrow）ansatz。
  - **步驟 2：最佳化問題**（行 ~800-900）：使用 Qiskit 的 pass manager 將電路轉譯為硬體相容。
  - **步驟 3：執行實驗**（行 ~900-1000）：透過 Qiskit Sampler 原語執行電路（包含錯誤緩解選項）。
  - **步驟 4：後處理結果**（行 ~1000-1500）：實作 SQD 迴圈，包括子取樣和對角化。
  - **練習**：互動任務，包括位元翻轉（Exercise 2）、基組變更（Exercise 3）、佈局選擇（Exercise 4）和 ansatz 修改（Exercise 5）（行 ~1500-結束）。
- **關鍵概念**：
  - SQD 透過將漢米爾頓量投影到從雜訊量子測量中取得的子空間來降低計算成本。
  - 使用 Jordan-Wigner 映射來處理費米子算符。
  - 強調硬體感知最佳化（例如，重金屬六邊形拓樸的 qubit 佈局）。
- **假設/限制**：假設存取 IBM Quantum 後端；專注於閉殼層分子如 N₂。沒有獨立的 README 或 docs 資料夾，但 notebook 本身有豐富註解和參考文獻（例如，UCJ ansatz 和 SQD 的論文）。

notebook 是教育性的，程式碼單元與 markdown 解釋交錯，使其自文件化。沒有明顯的外部 docs 資料夾，因此此檔案是主要來源。

## 2. 特定類型定義和介面
程式碼依賴外部函式庫（詳見第 4 節），但透過函式簽名隱含定義或使用關鍵類型。沒有明確的自訂類型（例如，類別），但從匯入使用相關介面：

- **來自 ffsim（量子電路算符）**：
  - `ffsim.UCJOpSpinBalanced`：自旋平衡 UCJ 算符類別。建構子：`from_t_amplitudes(t2, t1, n_reps, interaction_pairs)`。傳回具有 `amplitudes` 屬性（NumPy 陣列，形狀為 `(n_reps, ...)` 的 J 和 K 矩陣）的算符物件。用於行 ~1000 的 ansatz 建構。
  - `ffsim.qiskit.UCJOpSpinBalancedJW(operator)`：JW 映射的 Qiskit 包裝器。介面：透過 `circuit.append(ucj_op, qubits)` 附加到 `QuantumCircuit`。位於 ffsim 的 Qiskit 整合模組（外部依賴）。
  - `ffsim.qiskit.PrepareHartreeFockJW(norb, nelec)`：準備 Hartree-Fock 狀態。介面：透過 `circuit.append(prep_hf, qubits)` 附加到電路。確保粒子數守恆。

- **來自 Qiskit（原語和轉譯）**：
  - `SamplerV2`（來自 `qiskit_ibm_runtime`）：取樣介面。建構子：`Sampler(mode=backend, options=...)`。方法：`run(circuits, shots=...)` 傳回 `SamplerResult`，包含 `data.meas`（位元字串陣列）。用於行 ~1000。
  - `generate_preset_pass_manager(optimization_level, backend, initial_layout)`：傳回 `StagedPassManager`。介面：`pm.run(circuit)` 轉譯為 ISA。自訂階段 `ffsim.qiskit.PRE_INIT` 用於閘門合併（行 ~900）。
  - `SamplerOptions`：運行時選項資料類（例如，`dynamical_decoupling.enable=True`）。用於啟用錯誤緩解。

- **自訂函式**（在 notebook 中定義，行 ~200-500）：
  - `diagonalize_fermionic_hamiltonian(hcore, eri, bit_array, ...)`：主要 SQD 函式。參數：`hcore`（NumPy 陣列，1-體積分）、`eri`（NumPy 陣列，2-體積分）、`bit_array`（NumPy 位元字串陣列）、`norb`（int）、`nelec`（tuple）等。傳回 `SCIResult`（自訂物件，包含 `energy`、`sci_state`）。內部呼叫 `solve_sci_batch`。
  - `solve_sci_batch(hcore, eri, configurations, ...)`：在子空間中求解特徵值問題。參數：類似上述，加上 `spin_sq`（float）。傳回 `SCIResult` 物件清單。使用 SciPy 的特徵值求解器。
  - `plot_energy_and_occupancy(result_history, exact_energy)`：視覺化函式。參數：`SCIResult` 清單、float。使用 Matplotlib 繪製能量誤差和軌道佔有率。

沒有明確介面（例如，protocols）；程式碼使用 Qiskit 生態系常見的 duck-typing。

## 3. 相關實作
notebook 將 SQD 實作為混合工作流程。關鍵程式碼區段：

- **分子漢米爾頓量建構**（行 ~500-600）：
  - 使用 PySCF 的 `Mole` 和 `RHF` 進行 SCF 計算。
  - 提取積分：`hcore, nuclear_repulsion_energy = cas.get_h1cas(mo)`（1-體）、`eri = pyscf.ao2mo.restore(...)`（2-體）。
  - 角色：準備 JW 映射的費米子算符。位置：notebook 單元 ~20-30。

- **Ansatz 建構**（行 ~600-700）：
  - `ucj_op = ffsim.UCJOpSpinBalanced.from_t_amplitudes(...)`：從 CCSD 振幅建構算符。
  - 電路組裝：附加 HF 準備和 UCJ 算符到 `QuantumCircuit`。
  - 角色：產生參數化電路用於變分狀態準備。在 Exercise 5 中修改以擴展互動（行 ~1900）。

- **電路最佳化**（行 ~800-900）：
  - `pass_manager = generate_preset_pass_manager(...)`；`pass_manager.pre_init = ffsim.qiskit.PRE_INIT`；`isa_circuit = pass_manager.run(circuit)`。
  - 角色：將邏輯 qubit 映射到物理 qubit，減少閘門數（例如，合併旋轉）。使用 `initial_layout` 符合硬體拓樸（Exercise 4，行 ~1600）。

- **執行**（行 ~900-1000）：
  - `sampler = Sampler(mode=backend, options=...)`；`job = sampler.run([isa_circuit], shots=...)`；`bit_array = pub_result.data.meas`。
  - 角色：從 QPU 收集 100k 位元字串樣本（使用 DD 和測量 twirling 緩解雜訊）。輸出 NumPy 位元字串陣列。

- **後處理（SQD 迴圈）**（行 ~1000-1500）：
  - `result = diagonalize_fermionic_hamiltonian(...)`：核心迴圈。迭代：子取樣位元字串、投影/對角化漢米爾頓量、更新佔有率。
  - `solve_sci_batch(...)`：使用 SciPy (`eigh`) 實作子空間對角化。計算能量和狀態。
  - `callback(results)`：記錄迭代（能量、子空間維度）。
  - 角色：自一致恢復；從原始樣本開始，透過迭代精煉（最多 `max_iterations=5`）。處理自旋對稱和 carryover。

- **視覺化**（行 ~1500-1600）：
  - `plot_energy_and_occupancy(...)`：使用 Matplotlib 繪製能量誤差（對數尺度）和軌道佔有率。
  - 角色：比較 SQD 能量與精確（CCSD）值；顯示收斂。

練習（行 ~1600-結束）實作位元翻轉（Exercise 2）、基組變更（Exercise 3）、佈局（Exercise 4）和 ansatz 調整（Exercise 5），包含評分器。

實作是模組化的，可重複用於更大工作流程。

## 4. 關鍵依賴及其角色
專案依賴數個 Python 套件，用於量子模擬和化學：

- **Qiskit (v1.x，匯入為 `qiskit`)**：核心框架。角色：電路建構（`QuantumCircuit`、`QuantumRegister`）、轉譯（`generate_preset_pass_manager`）和原語（`SamplerV2` 用於執行）。關鍵用於硬體整合（例如，IBM 後端）。版本檢查：`print(f"Qiskit version: {qiskit.__version__}")`（行 ~10）。
- **Qiskit IBM Runtime (v0.40+)**：後端存取和取樣。角色：`QiskitRuntimeService` 用於作業提交（`service.backend(...)`）、`Sampler` 用於執行（包含 DD）。處理雜訊緩解。
- **PySCF**：量子化學後端。角色：建構分子（`Mole`）、執行 SCF/CCSD（`RHF`、`CCSD`）、提取積分（`get_h1cas`、`get_h2cas`）。漢米爾頓量產生不可或缺（行 ~500-600）。
- **ffsim**：專用於費米子模擬。角色：JW 映射和 ansatz 算符（`UCJOpSpinBalancedJW`、`PrepareHartreeFockJW`）。最佳化 Qiskit（例如，`PRE_INIT` 中的閘門合併）。關鍵用於有效電路深度。
- **NumPy (匯入為 `np`)**：陣列操作。角色：位元字串處理（`bit_array`）、矩陣操作（例如，`np.load`、特徵值計算）。在數值區段無所不在。
- **Matplotlib (匯入為 `plt`)**：繪圖。角色：視覺化結果（`plot_energy_and_occupancy`）。用於 ~5 個單元繪製能量/佔有率圖。
- **SciPy**：特徵值求解。角色：在 `solve_sci_batch` 中使用 `scipy.linalg.eigh` 進行子空間對角化。
- **其他**：`warnings`（抑制警告）、`partial`（來自 `functools`，用於 currying 求解器）、`pickle`（載入後端資料）。

依賴透過 pip 安裝（隱含：`pip install qiskit qiskit-ibm-runtime pyscf ffsim numpy matplotlib scipy`）。沒有自訂 package.json 或 requirements.txt；假設標準 Qiskit 環境。

此分析涵蓋專案核心。如需特定查詢（例如，「解釋 SQD 迴圈實作」或「如何修改為開殼層系統？」），請提供細節以獲得更針對性的回應！

**檔案資訊**：此內容可直接複製到 Markdown 檔案（例如 `sqd_analysis.md`）中保存。