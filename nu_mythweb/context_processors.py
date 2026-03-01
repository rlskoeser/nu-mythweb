from nu_mythweb.recordings.mythtv_service import MythTVService


def channel_list(request):
    """
    Injects the channel dictionary into every template context.
    The service already handles the caching logic.
    """
    # get list of channels; convert to dict for lookup/display
    channels_dict = {
        c["ChanId"]: f"{c['CallSign']} - {c['ChannelName']}"
        for c in MythTVService().get_channels()
    }
    return {"CHANNELS_DICT": channels_dict}
