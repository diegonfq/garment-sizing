import sizes
import logging

def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Basic
    standard_t_shirt = sizes.Tshirt(base_size="S")
    logging.debug("--- Initial Sizing Chart ---")
    logging.debug(standard_t_shirt.sizes)
    logging.debug(standard_t_shirt.deltas)

    # Override a value in the size 'M' (e.g. change in chest size)
    standard_t_shirt.override(measurement="Chest circumference", size="M", new_value=112.0)

    logging.debug("\n--- Sizing Chart After Updating Size 'M' ---")
    logging.debug(standard_t_shirt.sizes)
    logging.debug(standard_t_shirt.deltas)

    # Change base size, and make a change to demonstrate change of base size
    standard_t_shirt.change_base_size(new_base_size="L")
    standard_t_shirt.override(measurement="Hip circumference", size="L", new_value=8.0)

    logging.debug("\n--- Sizing Chart After Updating Base Size to 'L' and making a change ---")
    logging.debug(standard_t_shirt.sizes)
    logging.debug(standard_t_shirt.deltas)

    # Change base (L) chest size
    standard_t_shirt.override(measurement="Chest circumference", size="L", new_value=None)

    logging.debug("\n--- Sizing Chart After Updating Base Size to 'L' and making a change ---")
    logging.debug(standard_t_shirt.sizes)
    logging.debug(standard_t_shirt.deltas)


if __name__ == "__main__":
    main()