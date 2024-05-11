# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import copy
import logging
import os
from typing import Any, Dict, Tuple

from lxml import etree
import json
import numpy as np
from minerl.env._multiagent import _MultiAgentEnv
from minerl.env._singleagent import _SingleAgentEnv
from minerl.herobraine.env_specs.navigate_specs import Navigate

logger = logging.getLogger(__name__)


class _FakeEnvMixin(object):
    """A fake environment for unit testing.

    Uses the info from a single agent environment.
    """

    def __init__(self, *args, **kwargs):
        super(_FakeEnvMixin, self).__init__(*args, **kwargs)

        # This NPZ was generated by navigate.
        # TODO: Make github issue for expanding pre_recored envs.
        # TODO: Fake envs should use env.sample and pre_recorded envs should feature real sampled data!
        # TODO: Move fake environments.
        self._fake_malmo_data = np.load(
            os.path.join(os.path.abspath(os.path.dirname(__file__)), 'info.npz'),
            allow_pickle=True)['arr_0'].tolist()
        # Patch data to add in the new metadata fields -- otherwise `env.reset()` will
        # crash.
        for stack in self._fake_malmo_data["inventory"]:
            stack['metadata'] = 0


    def _setup_instances(self) -> None:
        self.instances = [NotImplemented for _ in range(self.task.agent_count)]

    def _send_mission(self, _, mission_xml_etree: etree.Element, token_in: str) -> None:
        logger.debug(
            "Sending fake XML for {}:".format(token_in)
            + etree.tostring(mission_xml_etree).decode())

    def _TO_MOVE_find_ip_and_port(self, _, token_in: str) -> Tuple[str, str]:
        return "1", "1"

    def _peek_obs(self) -> Dict[str, Any]:
        r, _ = self._get_fake_obs()
        return r

    def step(self, action) -> Tuple[
        Dict[str, Dict[str, Any]], Dict[str, float], Dict[str, bool], Dict[str, Dict[str, Any]]]:
        fobs, monitor = self._get_fake_obs()
        done = False
        reward = {a: 0.0 for a in self.task.agent_names}
        for actor_name in self.task.agent_names:
            cmd = self._process_action(actor_name, action[actor_name])
        # TODO: Abstract the malmo communication out of the step function.p

        return fobs, reward, done, monitor

    def _get_fake_obs(self) -> Dict[str, Any]:

        obs = {}
        info = {}
        for agent in self.task.agent_names:
            malmo_data = self._get_fake_malmo_data()
            pov = malmo_data['pov']
            del malmo_data['pov']
            pov = pov[::-1, :, :]
            _json_info = json.dumps(malmo_data)

            obs[agent], info[agent] = self._process_observation(agent, pov, _json_info)
        # TODO: UPDATE INFO FOR MONITORS!
        return obs, info

    def _get_fake_malmo_data(self) -> Dict[str, Any]:
        assert isinstance(self.task, Navigate), (
            "the data for fake environments was generated by Navigate")
        return copy.deepcopy(self._fake_malmo_data)


class _FakeMultiAgentEnv(_FakeEnvMixin, _MultiAgentEnv):
    """The fake multiagent environment."""
    pass


class _FakeSingleAgentEnv(_FakeEnvMixin, _SingleAgentEnv):
    """The fake singleagent environment."""

    def step(self, action):
        # Gets the resulting s,r,d,i pair from super but
        # but returns s[self.task.agent_names[0]], ...
        aname = self.task.agent_names[0]
        multi_agent_action = {
            aname: action
        }
        s, reward, done, info = super().step(multi_agent_action)
        return s[aname], reward[aname], done, info[aname]