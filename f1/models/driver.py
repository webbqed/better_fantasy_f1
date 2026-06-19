class Driver:
    def __init__(self, full_name, driver_number, team_name, win_prob=None, dnf_prob=None,
                 expected_finish=None, theta=None, sim_results=None, sim_points=None,
                 sim_mean=None, sim_std=None, price=None):
        self.full_name = full_name
        self.driver_number = driver_number
        self.team_name = team_name
        self.win_prob = win_prob
        self.dnf_prob = dnf_prob
        self.expected_finish = expected_finish
        self.theta = theta
        self.sim_results = sim_results
        self.sim_points = sim_points
        self.sim_mean = sim_mean
        self.sim_std = sim_std
        self.price = price

    def __str__(self):
        return f"Driver: {self.full_name} | Team: {self.team_name} | Avg Finish: {self.expected_finish}"

    def get_info(self):
        return {
            "full_name": self.full_name,
            "driver_number": self.driver_number,
            "team_name": self.team_name,
            "win_prob": self.win_prob,
            "dnf_prob": self.dnf_prob,
            "expected_finish": self.expected_finish,
            "theta": self.theta,
            "sim_results": self.sim_results,
            "sim_points": self.sim_points,
            "sim_mean": self.sim_mean,
            "sim_std": self.sim_std,
            "price": self.price,
        }
