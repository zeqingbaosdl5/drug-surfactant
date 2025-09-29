# Drug-Surfactant Optimization with opentrons.execute

This repository now includes a Python script-based implementation that replaces the Jupyter notebook workflow with `opentrons.execute` for protocol execution.

## New Implementation

### Files Added

1. **`protocol_executor.py`** - Main execution script that replaces the Jupyter notebook workflow
2. **`api_server.py`** - FastAPI server for cloud-hosted execution (Railway deployment)
3. **`helper_functions_fixed.py`** - Updated helper functions compatible with current ax-platform
4. **`requirements.txt`** - Dependencies for the new implementation

### Key Features

- **Command-line execution**: Run optimization directly from command line
- **FastAPI API**: Cloud-hosted execution via Railway or similar platforms
- **opentrons.execute integration**: Direct protocol execution instead of notebook
- **Backwards compatibility**: Works with existing protocol files
- **Flexible deployment**: Local, simulation, or hardware execution modes

## Usage

### Command Line

```bash
# Install dependencies
pip install -r requirements.txt

# Run optimization with simulation (default)
python protocol_executor.py --trials 5 --simulate

# Run on actual hardware
python protocol_executor.py --trials 5 --hardware

# Custom configuration
python protocol_executor.py --trials 10 --config config.json
```

### API Server (for Railway deployment)

```bash
# Start the FastAPI server
python api_server.py

# Or use uvicorn directly
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### API Endpoints

- `GET /` - API information
- `POST /experiments/start` - Start new optimization experiment
- `GET /experiments/{id}/status` - Check experiment status
- `GET /experiments/{id}/results` - Get experiment results
- `POST /protocols/execute` - Execute single protocol
- `GET /health` - Health check

### Example API Usage

```python
import requests

# Start an experiment
response = requests.post('http://localhost:8000/experiments/start', 
                        json={'config': {'optimization_trials': 5, 'simulate': True}})
experiment_id = response.json()['experiment_id']

# Check status
status = requests.get(f'http://localhost:8000/experiments/{experiment_id}/status')
print(status.json())

# Get results when complete
results = requests.get(f'http://localhost:8000/experiments/{experiment_id}/results')
print(results.json())
```

## Configuration

### Robot Connection Config

```json
{
    "remote_user": "root",
    "remote_host": "192.168.10.143",
    "remote_folder": "/var/lib/jupyter/notebooks/Zeqing_Bao/drug_surfactant",
    "optimization_trials": 5,
    "batch_size": 1,
    "simulate": true
}
```

## Migration from Jupyter Notebook

The new implementation maintains the same optimization logic and protocol structure as the original Jupyter notebook but provides:

1. **Better automation**: No manual cell execution required
2. **Cloud deployment**: Can be deployed on Railway, Heroku, etc.
3. **API access**: Programmatic access to optimization functionality
4. **Better error handling**: Robust execution with proper error management
5. **Scalability**: Background task execution for long-running experiments

## Protocol Execution

The system uses `opentrons.execute` for protocol execution:

- **Simulation mode**: Protocols are validated and executed in simulation
- **Hardware mode**: Protocols are transferred to robot via SSH/SCP and executed
- **Error handling**: Proper error reporting and recovery

## Cloud Deployment (Railway)

For deployment on Railway:

1. Connect your repository to Railway
2. Set environment variables as needed
3. Railway will automatically detect the Python app and run it
4. The `PORT` environment variable is automatically set by Railway

The API server is configured to work with Railway's deployment model.