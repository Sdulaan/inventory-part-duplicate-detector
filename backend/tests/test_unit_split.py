from app.engine.identity_edge import IdentityEdgeClass
from app.resolution.unit_split import split_oversized_unit, split_reference

STRONG = IdentityEdgeClass.STRONG_SUPPORT
REVIEW = IdentityEdgeClass.REVIEW_SUPPORT
NEUTRAL = IdentityEdgeClass.NON_GROUPABLE


def _clique(members, edge_class=STRONG, generic=False):
    return {
        (left, right): (edge_class, generic)
        for index, left in enumerate(members)
        for right in members[index + 1:]
    }


def test_positive_components_become_pieces_and_neutral_links_do_not_join_them():
    lookup = {**_clique((1, 2, 3)), **_clique((4, 5)), (3, 4): (NEUTRAL, False)}
    pieces, oversized = split_oversized_unit((1, 2, 3, 4, 5, 6), lookup, 3)
    assert pieces == ((1, 2, 3), (4, 5))
    assert oversized == ()


def test_weakest_links_are_dropped_first_until_pieces_fit():
    lookup = {
        **_clique((1, 2, 3)),
        **_clique((4, 5, 6)),
        (3, 4): (REVIEW, True),  # generic-only review link bridges the cliques
    }
    pieces, oversized = split_oversized_unit((1, 2, 3, 4, 5, 6), lookup, 3)
    assert pieces == ((1, 2, 3), (4, 5, 6))
    assert oversized == ()


def test_strong_cliques_larger_than_the_cap_stay_oversized():
    pieces, oversized = split_oversized_unit(
        (1, 2, 3, 4, 5), _clique((1, 2, 3, 4, 5)), 3
    )
    assert pieces == ()
    assert oversized == ((1, 2, 3, 4, 5),)


def test_piece_references_are_unique_per_piece():
    assert split_reference("n-1|n-2", (4, 5)) == "n-1|n-2#split:4"
    assert split_reference("n-1|n-2", (4, 5)) != split_reference("n-1|n-2", (1, 2))
