from tree_sitter import Language

Language.build_library(
    # Store the library in the `build` directory
    "../../libs/treesitter_c.so",
    # Include one or more languages
    ["tree-sitter-c"],
)