import asyncio
import pytest
import logging
import pubnub as pn

from pubnub.models.consumer.presence import PNSetStateResult, PNGetStateResult
from pubnub.pubnub_asyncio import AsyncioSubscriptionManager, PubNubAsyncio
from tests.helper import pnconf, pnconf_copy, pnconf_sub_copy, pnconf_pam_copy
from tests.integrational.vcr_asyncio_sleeper import VCR599Listener
from tests.integrational.vcr_helper import pn_vcr


pn.set_stream_logger('pubnub', logging.DEBUG)


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/state/single_channel.yaml',
    filter_query_parameters=['uuid', 'pnsdk'],
    match_on=['method', 'host', 'path', 'state_object_in_query'])
@pytest.mark.asyncio
async def test_single_channel():
    pubnub = PubNubAsyncio(pnconf_copy())
    ch = 'test-state-asyncio-ch'
    pubnub.config.uuid = 'test-state-asyncio-uuid'
    state = {"name": "Alex", "count": 5}

    env = await pubnub.set_state() \
        .channels(ch) \
        .state(state) \
        .future()

    assert env.result.state['name'] == "Alex"
    assert env.result.state['count'] == 5

    env = await pubnub.get_state() \
        .channels(ch) \
        .future()

    assert env.result.channels[ch]['name'] == "Alex"
    assert env.result.channels[ch]['count'] == 5

    await pubnub.stop()


@pytest.mark.asyncio
async def test_single_channel_with_subscription():
    pnconf = pnconf_sub_copy()
    pnconf.set_presence_timeout(12)
    pubnub = PubNubAsyncio(pnconf)
    ch = 'test-state-asyncio-ch-with-subscription'
    pubnub.config.uuid = 'test-state-asyncio-uuid-with-subscription'
    state = {"name": "Alex", "count": 5}

    callback = VCR599Listener(1)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels(ch).execute()

    await callback.wait_for_connect()
    await asyncio.sleep(20)

    env = await pubnub.set_state() \
        .channels(ch) \
        .state(state) \
        .future()

    assert env.result.state['name'] == "Alex"
    assert env.result.state['count'] == 5

    env = await pubnub.get_state() \
        .channels(ch) \
        .future()

    assert env.result.channels[ch]['name'] == "Alex"
    assert env.result.channels[ch]['count'] == 5

    pubnub.unsubscribe().channels(ch).execute()
    if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
        await callback.wait_for_disconnect()

    await pubnub.stop()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/state/multiple_channel.yaml',
    filter_query_parameters=['uuid', 'pnsdk'],
    match_on=['method', 'host', 'path', 'state_object_in_query'])
@pytest.mark.asyncio
async def test_multiple_channels():
    pubnub = PubNubAsyncio(pnconf)
    ch1 = 'test-state-asyncio-ch1'
    ch2 = 'test-state-asyncio-ch2'
    pubnub.config.uuid = 'test-state-asyncio-uuid'
    state = {"name": "Alex", "count": 5}

    env = await pubnub.set_state() \
        .channels([ch1, ch2]) \
        .state(state) \
        .future()

    assert env.result.state['name'] == "Alex"
    assert env.result.state['count'] == 5

    env = await pubnub.get_state() \
        .channels([ch1, ch2]) \
        .future()

    assert env.result.channels[ch1]['name'] == "Alex"
    assert env.result.channels[ch2]['name'] == "Alex"
    assert env.result.channels[ch1]['count'] == 5
    assert env.result.channels[ch2]['count'] == 5

    await pubnub.stop()


@pytest.mark.asyncio
async def test_state_super_admin_call():
    pnconf = pnconf_pam_copy()
    pubnub = PubNubAsyncio(pnconf)
    ch1 = 'test-state-asyncio-ch1'
    ch2 = 'test-state-asyncio-ch2'
    pubnub.config.uuid = 'test-state-asyncio-uuid-|.*$'
    state = {"name": "Alex", "count": 5}

    env = await pubnub.set_state() \
        .channels([ch1, ch2]) \
        .state(state) \
        .future()
    assert isinstance(env.result, PNSetStateResult)

    env = await pubnub.get_state() \
        .channels([ch1, ch2]) \
        .future()
    assert isinstance(env.result, PNGetStateResult)

    await pubnub.stop()
