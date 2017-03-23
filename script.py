import cPickle as pickle

from argparse import ArgumentParser


def get_parser():
    """ Returns argument parser. """
    parser = ArgumentParser(
        description="A command line tool to provide useful information for " +
        "the housing lottery."
    )
    parser.add_argument(
        "-s",
        "--size",
        type=int,
        help="Option to retrieve list of housing groups by a specified size."
    )
    parser.add_argument(
        "-o",
        "--old",
        action="store_true",
        default=False,
        help="Flag to get old stats from previous year"
    )

    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    if args.size is not None:
        if args.old:
            from housing import Housing, Group, GroupID, Student  # noqa: F401
            with open("./data/old_housing_data.pkl", 'rb') as housing_data_f:
                housing_data = pickle.load(housing_data_f)

        else:
            from housing_17 import Housing, Group, GroupID, Student  # noqa: F401
            with open("./data/housing_data.pkl", 'rb') as housing_data_f:
                housing_data = pickle.load(housing_data_f)

        groups = housing_data.groups_by_size[args.size - 1]
        for i in range(len(groups)):
            group = groups[i]
            print("{:<5d}{:2.4f}  {:d}") \
                .format(i + 1, group.priority,
                        group.lottery_number)
