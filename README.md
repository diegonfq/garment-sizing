# Size chart

A Python-based tool for creating and managing dynamic garment sizing charts using Polars. 

### Key Features
- Dynamic Base Sizing: Set any size (e.g., S, M, L) as the base anchor and all other sizes will calculate automatically.
- Rule Validation: Automatically warns you if a larger size has a smaller measurement than a smaller size.
- Data Sanitisation: Automatically converts impossible measurements (e.g., negative lengths) to null.
- Save and load complete garment specifications, including all base values, deltas, and configurations.

### Premises
Premise 1: if a value for a base size is null, the whole row must be null (how would you calculate differences
if you have a null value?

Premise 2: when a delta is changed, a recalculation is not automatically triggered; the user must trigger it by
updating the corresponding value for the base size

Premise 3: user intent -- if a user manually overrides a size (non base), only that size (and its corresponding delta)
will change; if a user overrides a base size, all values in that row will update.

## Installation
1. Clone the repository:

```console
git clone https://github.com/diegonfq/size-chart.git
cd size-chart
```

2. Create and activate a virtual environment:

```console
python -m venv .venv

# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

3. Install the required packages:
```console
pip install -r requirements.txt
```

## Usage

```python
import sizes

# Creates a T-Shirt with base size set to small
standard_t_shirt = sizes.Tshirt(base_size="S")

# Changes the chest size of the medium T-Shirt, without affecting other sizes
standard_t_shirt.override(measurement="Chest circumference", size="M", new_value=112.0)

# Changes base size to large
standard_t_shirt.change_base_size(new_base_size="L")

# Displays a table with the sizes and another with the differences (base size 
# will have all deltas at 0, since all sizes are based around the base size
print(standard_t_shirt.sizes)
print(standard_t_shirt.deltas)
```

## License

[MIT](https://choosealicense.com/licenses/mit/)