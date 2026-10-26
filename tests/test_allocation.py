import unittest
from customer_profitability.allocation import compare_allocations, threshold_comparison
from customer_profitability.synthetic import build_synthetic_dataset


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.data = build_synthetic_dataset().transactions

    def test_pool_conserved_and_direct_profit_preserved(self):
        output = compare_allocations(self.data, 50000)
        for _, part in output.groupby('allocation_driver'):
            self.assertAlmostEqual(part.allocated_shared_cost.sum(), 50000)
            self.assertAlmostEqual((part.contribution_profit-part.after_shared_cost_profit).sum(), 50000)
        # Synthetic dataset contains equal order counts for five customers.
        self.assertTrue(output.query("allocation_driver=='order_count'").allocated_shared_cost.eq(10000).all())

    def test_zero_and_invalid_pool(self):
        self.assertTrue(compare_allocations(self.data, 0).allocated_shared_cost.eq(0).all())
        for value in (-1, float('nan'), float('inf'), True):
            with self.assertRaises(ValueError):
                compare_allocations(self.data, value)

    def test_thresholds_do_not_change_profit_ranking(self):
        detail, stability = threshold_comparison(self.data)
        self.assertEqual(len(detail), 15)
        self.assertTrue(stability.distinct_profit_ranks.eq(1).all())
