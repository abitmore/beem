from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from builtins import super
import mock
import string
import unittest
import random
from pprint import pprint
from beem import Steem
from beem.amount import Amount
from beem.witness import Witness
from beem.account import Account
from beem.instance import set_shared_steem_instance
from beem.blockchain import Blockchain
from beem.block import Block
from beem.wallet import Wallet
from beemgraphenebase.account import PasswordKey, PrivateKey, PublicKey
from beem.utils import parse_time, formatTimedelta
from beemgrapheneapi.rpcutils import NumRetriesReached

# Py3 compatibility
import sys
wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]
core_unit = "GLS"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_shared_steem_instance(None)
        self.stm = Steem(
            node=nodes,
            nobroadcast=True,
            bundle=False,
            # Overwrite wallet to use this list of wifs only
            wif={"active": wif}
        )
        self.bts = Steem(
            node=["wss://ws.golos.io"],
            keys={"active": wif, "owner": wif, "posting": wif},
            nobroadcast=True,
        )
        # from getpass import getpass
        # self.bts.wallet.unlock(getpass())

    def test_transfer(self):
        bts = self.bts
        # bts.prefix ="STX"
        acc = Account("test", steem_instance=bts)
        tx = acc.transfer(
            "test1", 1.33, "GBG", memo="Foobar")
        self.assertEqual(
            tx["operations"][0][0],
            "transfer"
        )
        op = tx["operations"][0][1]
        self.assertIn("memo", op)
        self.assertEqual(op["from"], "test")
        self.assertEqual(op["to"], "test1")
        amount = Amount(op["amount"], steem_instance=bts)
        self.assertEqual(float(amount), 1.33)

    def test_create_account(self):
        bts = self.bts
        name = ''.join(random.choice(string.ascii_lowercase) for _ in range(12))
        key1 = PrivateKey()
        key2 = PrivateKey()
        key3 = PrivateKey()
        key4 = PrivateKey()
        key5 = PrivateKey()
        tx = bts.create_account(
            name,
            creator="test",
            owner_key=format(key1.pubkey, core_unit),
            active_key=format(key2.pubkey, core_unit),
            posting_key=format(key3.pubkey, core_unit),
            memo_key=format(key4.pubkey, core_unit),
            additional_owner_keys=[format(key5.pubkey, core_unit)],
            additional_active_keys=[format(key5.pubkey, core_unit)],
            additional_owner_accounts=["test1"],  # 1.2.0
            additional_active_accounts=["test1"],
            storekeys=False
        )
        self.assertEqual(
            tx["operations"][0][0],
            "account_create"
        )
        op = tx["operations"][0][1]
        role = "active"
        self.assertIn(
            format(key5.pubkey, core_unit),
            [x[0] for x in op[role]["key_auths"]])
        self.assertIn(
            format(key5.pubkey, core_unit),
            [x[0] for x in op[role]["key_auths"]])
        self.assertIn(
            "test1",
            [x[0] for x in op[role]["account_auths"]])
        role = "owner"
        self.assertIn(
            format(key5.pubkey, core_unit),
            [x[0] for x in op[role]["key_auths"]])
        self.assertIn(
            format(key5.pubkey, core_unit),
            [x[0] for x in op[role]["key_auths"]])
        self.assertIn(
            "test1",
            [x[0] for x in op[role]["account_auths"]])
        self.assertEqual(
            op["creator"],
            "test")

    def test_connect(self):
        bts = self.bts
        self.assertEqual(bts.prefix, "GLS")

    def test_info(self):
        info = self.bts.info()
        for key in ['current_witness',
                    'head_block_id',
                    'head_block_number',
                    'id',
                    'last_irreversible_block_num',
                    'current_witness',
                    'total_pow',
                    'time']:
            self.assertTrue(key in info)

    def test_finalizeOps(self):
        bts = self.bts
        tx1 = bts.new_tx()
        tx2 = bts.new_tx()

        acc = Account("test", steem_instance=bts)
        acc.transfer("test1", 1, "GOLOS", append_to=tx1)
        acc.transfer("test1", 2, "GOLOS", append_to=tx2)
        acc.transfer("test1", 3, "GOLOS", append_to=tx1)
        tx1 = tx1.json()
        tx2 = tx2.json()
        ops1 = tx1["operations"]
        ops2 = tx2["operations"]
        self.assertEqual(len(ops1), 2)
        self.assertEqual(len(ops2), 1)

    def test_weight_threshold(self):
        bts = self.bts
        auth = {'account_auths': [['test', 1]],
                'extensions': [],
                'key_auths': [
                    ['GLS55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n', 1],
                    ['GLS7GM9YXcsoAJAgKbqW2oVj7bnNXFNL4pk9NugqKWPmuhoEDbkDv', 1]],
                'weight_threshold': 3}  # threshold fine
        bts._test_weights_treshold(auth)
        auth = {'account_auths': [['test', 1]],
                'extensions': [],
                'key_auths': [
                    ['GLS55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n', 1],
                    ['GLS7GM9YXcsoAJAgKbqW2oVj7bnNXFNL4pk9NugqKWPmuhoEDbkDv', 1]],
                'weight_threshold': 4}  # too high

        with self.assertRaises(ValueError):
            bts._test_weights_treshold(auth)

    def test_allow(self):
        bts = self.bts
        self.assertIn(bts.prefix, "GLS")
        acc = Account("test", steem_instance=bts)
        self.assertIn(acc.steem.prefix, "GLS")
        tx = acc.allow(
            "GLS55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n",
            account="test",
            weight=1,
            threshold=1,
            permission="owner",
        )
        self.assertEqual(
            (tx["operations"][0][0]),
            "account_update"
        )
        op = tx["operations"][0][1]
        self.assertIn("owner", op)
        self.assertIn(
            ["GLS55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n", '1'],
            op["owner"]["key_auths"])
        self.assertEqual(op["owner"]["weight_threshold"], 1)

    def test_disallow(self):
        bts = self.bts
        acc = Account("test", steem_instance=bts)
        if sys.version > '3':
            _assertRaisesRegex = self.assertRaisesRegex
        else:
            _assertRaisesRegex = self.assertRaisesRegexp
        with _assertRaisesRegex(ValueError, ".*Changes nothing.*"):
            acc.disallow(
                "GLS55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n",
                weight=1,
                threshold=1,
                permission="owner"
            )
        with _assertRaisesRegex(ValueError, ".*Changes nothing!.*"):
            acc.disallow(
                "GLS6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV",
                weight=1,
                threshold=1,
                permission="owner"
            )

    def test_update_memo_key(self):
        bts = self.bts
        self.assertEqual(bts.prefix, "GLS")
        acc = Account("test", steem_instance=bts)
        tx = acc.update_memo_key("GLS55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n")
        self.assertEqual(
            (tx["operations"][0][0]),
            "account_update"
        )
        op = tx["operations"][0][1]
        self.assertEqual(
            op["memo_key"],
            "GLS55VCzsb47NZwWe5F3qyQKedX9iHBHMVVFSc96PDvV7wuj7W86n")

    def test_approvewitness(self):
        bts = self.bts
        w = Account("test", steem_instance=bts)
        tx = w.approvewitness("test1")
        self.assertEqual(
            (tx["operations"][0][0]),
            "account_witness_vote"
        )
        op = tx["operations"][0][1]
        self.assertIn(
            "test1",
            op["witness"])