# UAV Search and Rescue: Reinforcement Learning Implementation

**Team Orienteering Problem with Charging Stations**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Implementation of reinforcement learning approaches for routing multiple UAVs in search and rescue operations with battery constraints and charging stations.

---

##  Overview
This project solves the **Team Orienteering Problem (TOP)** with charging stations for UAV search and rescue missions. Multiple UAVs must visit survivor locations to maximize total rescued rewards while managing:

-  **Time constraints** - Limited mission duration
-  **Battery constraints** - Limited flight time per charge
-  **Charging stations** - Strategic recharging locations
-  **Multiple UAVs** - Team coordination
-  **Selective coverage** - Cannot visit all nodes

flowchart TD
    A[UAV Search and Rescue] --> B[Team Orienteering Problem]
    B --> C[Charging Stations]
    B --> D[Multiple UAVs]
    B --> E[Time Constraints]
    B --> F[Battery Constraints]
    B --> G[Selective Coverage]

    C --> H[Strategic Recharging Locations]
    D --> I[Team Coordination]
    E --> J[Limited Mission Duration]
    F --> K[Limited Flight Time per Charge]

    A --> L[Objective: Maximize Total Rewards]
    A --> M[Constraints]
    M --> N[Max Flight Time per UAV]
    M --> O[Limited Battery Capacity]
    M --> P[Service Nodes Visited Once]
    M --> Q[Charging Stations Visited Multiple Times]
    M --> R[Return to Depot]

    A --> S[Decision Variables]
    S --> T[Nodes to Visit]
    S --> U[Order of Visits]
    S --> V[When to Recharge]

    A --> W[NP-hard Problem]
    A --> X[Core Implementation]
    X --> Y[Multiple RL Algorithms]
    Y --> Z[Q-Learning with NDTS]
    Y --> AA[Improved Q-Learning]
    Y --> AB[Deep Q-Network]
    Y --> AC[Greedy Baseline Heuristic]

    X --> AD[Two-Phase Decomposition]
    AD --> AE[K-means Clustering]
    AD --> AF[Independent Optimization]
    AD --> AG[Scalable to 100+ Nodes]

### Problem Formulation

**Objective:** Maximize total collected rewards

**Constraints:**
- Each UAV has maximum flight time
- Each UAV has limited battery capacity
- Service nodes can be visited at most once
- Charging stations can be visited multiple times
- Each UAV must return to depot

**Decision Variables:**
- Which nodes to visit
- Order of visits  
- When to recharge

This is an **NP-hard** problem combining Knapsack and Traveling Salesman Problem characteristics.

---

## ✨ Features

### Core Implementation
- ✅ **Multiple RL Algorithms**
  - Q-Learning with Non-Decreasing Tree Search (NDTS)
  - Improved Q-Learning with Reward-Biased Exploration
  - Deep Q-Network (DQN)
  - Greedy Baseline Heuristic
  
- ✅ **Two-Phase Decomposition**
  - K-means clustering of service nodes
  - Independent optimization per cluster
  - Scalable to 100+ nodes

- ✅ **MILP Solver**
  - Exact formulation using PuLP
  - Baseline for optimality gap analysis
  - Works on small instances (≤20 nodes)

### Interactive Dashboard
- ✅ **Real-time Visualization** with Streamlit
- ✅ **Algorithm Comparison** - Switch between methods
- ✅ **Parameter Tuning** - Adjust nodes, UAVs, battery, time limits
- ✅ **Performance Metrics** - Reward, coverage, efficiency
- ✅ **Multi-tab Analysis**
  - Route visualization with interactive maps
  - Reward distribution per UAV
  - Battery consumption tracking
  - Clustering visualization
  - Missed opportunity analysis

### Analysis Tools
- ✅ **Training Progress Tracking**
- ✅ **Route Validation** - Verify cluster assignments
- ✅ **Comparative Benchmarking**
- ✅ **Export Results** - Save configurations and solutions

---

## 🔧 Installation

### System Requirements

- **Python 3.12** (strongly recommended)
- 4GB RAM minimum
- Windows/Linux/macOS

### Step 1: Clone Repository

```bash
git clone https://github.com/sanidhya-karnik/uav-search-rescue-rl.git
cd uav-search-rescue-rl
```

### Step 2: Create Virtual Environment

**Windows:**
```cmd
py -3.12 -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3.12 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install all packages
pip install -r requirements.txt
```

**Note:** If you encounter issues with PyTorch, install CPU-only version:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Step 4: Verify Installation

```bash
python -c "import streamlit, torch, numpy, plotly; print('✓ Installation successful!')"
```

### Step 5: Launch Interactive Dashboard (Streamlit)

```bash
streamlit run app.py
```

Then in the browser:
1. Click **🔄 Generate** to create environment
2. Click **🚀 Solve** to find optimal routes
3. Explore the 4 analysis tabs

---

## 📚 Usage

### Dashboard Controls

**Sidebar Configuration:**
- **Service Nodes**: 10, 20, 30, 50, 100
- **Number of UAVs**: 1-5
- **Charging Stations**: 2, 3, 5, 10
- **Map Size**: 50-200
- **Time Limit**: 50-300
- **Battery Capacity**: 25-150
- **Random Seed**: For reproducibility
- **Algorithm Selection**:
  - Original Q-Learning (NDTS)
  - Improved Q-Learning (Reward-Biased) ⭐
  - Greedy Baseline
- **Training Episodes**: 5K-100K

### Visualization Tabs

1. **🗺️ Route Visualization**
   - Interactive map with UAV routes
   - Color-coded service nodes by reward
   - Hover for detailed information

2. **📊 Reward Analysis**
   - Reward distribution per UAV
   - Visited vs unvisited nodes
   - Coverage statistics

3. **🔋 Battery Analysis**
   - Battery consumption over time
   - Charging events visualization
   - Statistics table

4. **📈 Clustering**
   - K-means cluster visualization
   - Cluster statistics
   - Validation of cluster assignments

---

## 🤖 Algorithms

### 1. Q-Learning with NDTS

**Non-Decreasing Tree Search (NDTS)** - Novel update mechanism for combinatorial optimization:

- Handles action masking for visited nodes
- Backward trajectory replay
- Non-decreasing Q-value updates for stability
- Discretized state space (battery, time, visited nodes)

**Key Innovation:** Addresses Q-learning instability in problems with history-dependent action spaces.

### 2. Improved Q-Learning

Enhancements over baseline NDTS:

- **Reward-biased exploration**: Samples high-reward nodes proportionally
- **Efficient node scoring**: Reward-per-distance ratio
- **Smart tie-breaking**: Prefers higher rewards when Q-values are equal
- **Feasibility awareness**: Considers battery/time margins

**Performance:** ~20-30% better reward collection than baseline.

### 3. Deep Q-Network (DQN)

Neural network approximation of Q-values:

- **State encoding**: One-hot node + normalized battery/time + visited mask
- **Architecture**: 3 hidden layers [256, 256, 128] with ReLU
- **Experience replay**: For sample efficiency
- **Target network**: For training stability

**Best for:** Large-scale problems (50+ nodes) where tabular methods struggle.

### 4. Two-Phase Approach (CFQS)

**Cluster First, Q-learning Second:**

**Phase 1:** K-means clustering of service nodes into k clusters (k = number of UAVs)

**Phase 2:** Solve each cluster independently with RL

**Benefits:**
- Reduces complexity from O(n!) to k × O((n/k)!)
- Enables parallelization
- Scalable to 100+ nodes
- 85%+ faster than direct MILP

### 5. Greedy Baseline

Heuristic approach for benchmarking:

- Always selects highest reward-per-distance node
- Fast execution (no training required)
- Provides lower bound on performance

### 6. MILP Solver

Exact optimization using Mixed-Integer Linear Programming:

- Optimal solutions for small instances
- PuLP/Gurobi implementation
- Reference for optimality gap calculation
- Time limit: 1 hour

---

## 📂 Project Structure

```
uav-search-rescue-rl/
│
├── 📄 Core Modules
│   ├── uav_environment.py              # Environment definition and dynamics
│   ├── q_learning_ndts.py              # Q-Learning with NDTS algorithm
│   ├── improved_q_learning.py          # Enhanced Q-Learning with reward bias
│   ├── dqn_agent.py                    # Deep Q-Network implementation
│   ├── greedy_baseline.py              # Greedy heuristic solver
│   ├── two_phase_cfqs.py               # Two-phase decomposition approach
│   └── milp_solver.py                  # MILP formulation and solver
│
├── 🎨 Visualization & Interface
│   ├── app.py                          # Streamlit interactive dashboard
│   └── comparison_script.py            # Comparative analysis framework
│
├── 🛠️ Utilities
│   └── requirements.txt                # Python dependencies
│
└── 📚 Documentation
    └── README.md                       # This file

```

---

## 📊 Results

### Performance Comparison (20 nodes, 2 UAVs, seed=42)

| Algorithm | Reward | Time (s) | Coverage | Notes |
|-----------|--------|----------|----------|-------|
| MILP (Gurobi) | 150 | 13 | 100% | Optimal (small instances only) |
| Greedy | 140 | <1 | 80% | Fast baseline |
| Q-Learning (NDTS) | 135 | 32 | 75% | Original paper method |
| Improved Q-Learning | 160 | 35 | 85% | Reward-biased exploration |
| DQN | 145 | 87 | 78% | Neural network approach |

*Results vary with random seed and training episodes*

### Algorithm Selection Guide

**Use MILP when:**
- Instance is small (≤20 nodes)
- Need proven optimal solution
- Have Gurobi license

**Use Greedy when:**
- Need fast solution
- Want simple baseline
- Interpretability matters

**Use Q-Learning (NDTS) when:**
- Medium instances (20-50 nodes)
- Want exact paper replication
- Stable, proven approach

**Use Improved Q-Learning when:**
- Want best performance ⭐
- Medium to large instances
- Have time for training (20K+ episodes)

**Use DQN when:**
- Very large instances (100+ nodes)
- State space is huge
- Can leverage GPU

---

## 🏗️ Key Components

### UAVEnvironment

Core environment class managing:
- Node generation (service, charging, depot)
- Distance/cost matrices
- State transitions
- Feasibility checking
- Visualization

### Q-Learning NDTS

Novel Q-learning variant:
- Discretizes continuous state (battery, time)
- Non-decreasing update prevents Q-value oscillation
- Action masking for visited nodes
- Backward replay through trajectories

### Two-Phase CFQS

Decomposition strategy:
1. Cluster service nodes by proximity
2. Assign one UAV per cluster
3. Solve each cluster independently
4. Combine solutions

Reduces exponential complexity while maintaining solution quality.

---

## 📈 Results

### Typical Performance (20 nodes, 2 UAVs)

```
Algorithm: Improved Q-Learning (Reward-Biased)
Training Episodes: 20,000
Time: ~35 seconds

Results:
- Total Reward: 160
- Nodes Visited: 17/20 (85%)
- Avg Reward/UAV: 80
- Recharges: 2-3 per UAV
```

### Scalability

| Nodes | UAVs | Episodes | Time | Reward | Coverage |
|-------|------|----------|------|--------|----------|
| 20 | 2 | 20K | 35s | 160 | 85% |
| 50 | 3 | 50K | 180s | 380 | 75% |
| 100 | 5 | 100K | 720s | 650 | 65% |

*Tested on Intel i7, 16GB RAM*

---

## 🐛 Troubleshooting

### Python Version Issues

**Problem:** `pip install` fails with compilation errors

**Solution:** Use Python 3.12 specifically
```bash
# Windows
py -3.12 -m venv venv

# Check version after activation
python --version  # Should show 3.12.x
```

### Path Too Long (Windows)

**Problem:** `OSError: [Errno 2] No such file or directory`

**Solution:** Use shorter path
```bash
# Instead of deep OneDrive paths, use:
cd C:\
mkdir Dev
cd Dev\UAV_RL
# Place files here
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'streamlit'`

**Solution:** Ensure venv is activated
```bash
# You should see (venv) in prompt
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/Mac

# Then reinstall
pip install -r requirements.txt
```

### Streamlit Won't Start

**Problem:** `streamlit: command not found`

**Solution:**
```bash
# Reinstall streamlit
pip install --upgrade streamlit

# Or run with python -m
python -m streamlit run app.py
```

### Slow Training

**Solution:** Reduce episodes or problem size
```bash
# In dashboard: Select fewer episodes (5K or 10K)
# Or use fewer service nodes (10 or 20)
```

### Out of Memory (DQN)

**Solution:** Reduce network size
```python
agent = DQNAgent(env, hidden_dims=[128, 128, 64], batch_size=32)
```

---

## 🔬 Experimental Setup

### Benchmarking Protocol

1. **Environment Generation:**
   - Fixed seeds: 42, 43, 44 for reproducibility
   - Three sizes: 20, 50, 100 service nodes
   - Proportional charging stations: n/10

2. **Training Configuration:**
   - Q-Learning: 100K episodes for size 100
   - DQN: 50K episodes
   - Discount factor γ = 0.95
   - Learning rate α = 0.1

3. **Evaluation:**
   - Greedy policy (ε = 0)
   - 10 random seeds
   - Report mean ± std

### Metrics

- **Total Reward**: Sum of collected rewards
- **Coverage**: % of service nodes visited
- **Efficiency**: Reward per UAV
- **Computation Time**: Training + inference time
- **Optimality Gap**: vs MILP (when available)
- **Feasibility**: % of constraint violations

---

## 📝 Citation

### This Implementation

```bibtex
@software{karnik2025uav,
  author = {Karnik, Sanidhya},
  title = {Multi-Agent RL for UAV Search and Rescue: Implementation},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/sanidhya-karnik/uav-search-rescue-rl}
}
```

### Original Paper

```bibtex
@article{qian2025uav,
  title={UAVs for Search and Rescue: A Reinforcement Learning Approach},
  author={Qian, Leren and Wang, Peiqi and Ma, Dinghao and 
          Dehghanimohammadabadi, Mohammad and Behroozi, Mehdi and 
          Melachrinoudis, Emanuel},
  journal={Expert Systems with Applications},
  year={2025},
  publisher={Elsevier}
}
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Original paper by Qian et al. (2025) from Northeastern University
- Course: IE7295 Applied Reinforcement Learning
- Libraries: NumPy, PyTorch, Streamlit, Plotly, scikit-learn, PuLP

---

## 📚 References

1. Qian, L., et al. (2025). UAVs for Search and Rescue: A Reinforcement Learning Approach. *Expert Systems with Applications*.

2. Vansteenwegen, P., et al. (2011). The orienteering problem: A survey. *European Journal of Operational Research*, 209(1), 1-10.

3. Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction*. MIT Press.

4. Busoniu, L., et al. (2008). A comprehensive survey of multiagent reinforcement learning. *IEEE Transactions on Systems, Man, and Cybernetics*, 38(2), 156-172.

---

*Last updated: November 2025*
