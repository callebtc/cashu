# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import warnings

import grpc
import lightning_pb2 as lightning__pb2
import router_pb2 as router__pb2

GRPC_GENERATED_VERSION = '1.63.0'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.65.0'
SCHEDULED_RELEASE_DATE = 'June 25, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + ' but the generated code in router_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class RouterStub(object):
    """
    Comments in this file will be directly parsed into the API
    Documentation as descriptions of the associated method, message, or field.
    These descriptions should go right above the definition of the object, and
    can be in either block or // comment format.

    An RPC method can be matched to an lncli command by placing a line in the
    beginning of the description in exactly the following format:
    lncli: `methodname`

    Failure to specify the exact name of the command will cause documentation
    generation to fail.

    More information on how exactly the gRPC documentation is generated from
    this proto file can be found here:
    https://github.com/lightninglabs/lightning-api

    Router is a service that offers advanced interaction with the router
    subsystem of the daemon.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SendPaymentV2 = channel.unary_stream(
                '/routerrpc.Router/SendPaymentV2',
                request_serializer=router__pb2.SendPaymentRequest.SerializeToString,
                response_deserializer=lightning__pb2.Payment.FromString,
                _registered_method=True)
        self.TrackPaymentV2 = channel.unary_stream(
                '/routerrpc.Router/TrackPaymentV2',
                request_serializer=router__pb2.TrackPaymentRequest.SerializeToString,
                response_deserializer=lightning__pb2.Payment.FromString,
                _registered_method=True)
        self.TrackPayments = channel.unary_stream(
                '/routerrpc.Router/TrackPayments',
                request_serializer=router__pb2.TrackPaymentsRequest.SerializeToString,
                response_deserializer=lightning__pb2.Payment.FromString,
                _registered_method=True)
        self.EstimateRouteFee = channel.unary_unary(
                '/routerrpc.Router/EstimateRouteFee',
                request_serializer=router__pb2.RouteFeeRequest.SerializeToString,
                response_deserializer=router__pb2.RouteFeeResponse.FromString,
                _registered_method=True)
        self.SendToRoute = channel.unary_unary(
                '/routerrpc.Router/SendToRoute',
                request_serializer=router__pb2.SendToRouteRequest.SerializeToString,
                response_deserializer=router__pb2.SendToRouteResponse.FromString,
                _registered_method=True)
        self.SendToRouteV2 = channel.unary_unary(
                '/routerrpc.Router/SendToRouteV2',
                request_serializer=router__pb2.SendToRouteRequest.SerializeToString,
                response_deserializer=lightning__pb2.HTLCAttempt.FromString,
                _registered_method=True)
        self.ResetMissionControl = channel.unary_unary(
                '/routerrpc.Router/ResetMissionControl',
                request_serializer=router__pb2.ResetMissionControlRequest.SerializeToString,
                response_deserializer=router__pb2.ResetMissionControlResponse.FromString,
                _registered_method=True)
        self.QueryMissionControl = channel.unary_unary(
                '/routerrpc.Router/QueryMissionControl',
                request_serializer=router__pb2.QueryMissionControlRequest.SerializeToString,
                response_deserializer=router__pb2.QueryMissionControlResponse.FromString,
                _registered_method=True)
        self.XImportMissionControl = channel.unary_unary(
                '/routerrpc.Router/XImportMissionControl',
                request_serializer=router__pb2.XImportMissionControlRequest.SerializeToString,
                response_deserializer=router__pb2.XImportMissionControlResponse.FromString,
                _registered_method=True)
        self.GetMissionControlConfig = channel.unary_unary(
                '/routerrpc.Router/GetMissionControlConfig',
                request_serializer=router__pb2.GetMissionControlConfigRequest.SerializeToString,
                response_deserializer=router__pb2.GetMissionControlConfigResponse.FromString,
                _registered_method=True)
        self.SetMissionControlConfig = channel.unary_unary(
                '/routerrpc.Router/SetMissionControlConfig',
                request_serializer=router__pb2.SetMissionControlConfigRequest.SerializeToString,
                response_deserializer=router__pb2.SetMissionControlConfigResponse.FromString,
                _registered_method=True)
        self.QueryProbability = channel.unary_unary(
                '/routerrpc.Router/QueryProbability',
                request_serializer=router__pb2.QueryProbabilityRequest.SerializeToString,
                response_deserializer=router__pb2.QueryProbabilityResponse.FromString,
                _registered_method=True)
        self.BuildRoute = channel.unary_unary(
                '/routerrpc.Router/BuildRoute',
                request_serializer=router__pb2.BuildRouteRequest.SerializeToString,
                response_deserializer=router__pb2.BuildRouteResponse.FromString,
                _registered_method=True)
        self.SubscribeHtlcEvents = channel.unary_stream(
                '/routerrpc.Router/SubscribeHtlcEvents',
                request_serializer=router__pb2.SubscribeHtlcEventsRequest.SerializeToString,
                response_deserializer=router__pb2.HtlcEvent.FromString,
                _registered_method=True)
        self.SendPayment = channel.unary_stream(
                '/routerrpc.Router/SendPayment',
                request_serializer=router__pb2.SendPaymentRequest.SerializeToString,
                response_deserializer=router__pb2.PaymentStatus.FromString,
                _registered_method=True)
        self.TrackPayment = channel.unary_stream(
                '/routerrpc.Router/TrackPayment',
                request_serializer=router__pb2.TrackPaymentRequest.SerializeToString,
                response_deserializer=router__pb2.PaymentStatus.FromString,
                _registered_method=True)
        self.HtlcInterceptor = channel.stream_stream(
                '/routerrpc.Router/HtlcInterceptor',
                request_serializer=router__pb2.ForwardHtlcInterceptResponse.SerializeToString,
                response_deserializer=router__pb2.ForwardHtlcInterceptRequest.FromString,
                _registered_method=True)
        self.UpdateChanStatus = channel.unary_unary(
                '/routerrpc.Router/UpdateChanStatus',
                request_serializer=router__pb2.UpdateChanStatusRequest.SerializeToString,
                response_deserializer=router__pb2.UpdateChanStatusResponse.FromString,
                _registered_method=True)


class RouterServicer(object):
    """
    Comments in this file will be directly parsed into the API
    Documentation as descriptions of the associated method, message, or field.
    These descriptions should go right above the definition of the object, and
    can be in either block or // comment format.

    An RPC method can be matched to an lncli command by placing a line in the
    beginning of the description in exactly the following format:
    lncli: `methodname`

    Failure to specify the exact name of the command will cause documentation
    generation to fail.

    More information on how exactly the gRPC documentation is generated from
    this proto file can be found here:
    https://github.com/lightninglabs/lightning-api

    Router is a service that offers advanced interaction with the router
    subsystem of the daemon.
    """

    def SendPaymentV2(self, request, context):
        """
        SendPaymentV2 attempts to route a payment described by the passed
        PaymentRequest to the final destination. The call returns a stream of
        payment updates. When using this RPC, make sure to set a fee limit, as the
        default routing fee limit is 0 sats. Without a non-zero fee limit only
        routes without fees will be attempted which often fails with
        FAILURE_REASON_NO_ROUTE.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TrackPaymentV2(self, request, context):
        """lncli: `trackpayment`
        TrackPaymentV2 returns an update stream for the payment identified by the
        payment hash.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TrackPayments(self, request, context):
        """
        TrackPayments returns an update stream for every payment that is not in a
        terminal state. Note that if payments are in-flight while starting a new
        subscription, the start of the payment stream could produce out-of-order
        and/or duplicate events. In order to get updates for every in-flight
        payment attempt make sure to subscribe to this method before initiating any
        payments.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def EstimateRouteFee(self, request, context):
        """
        EstimateRouteFee allows callers to obtain a lower bound w.r.t how much it
        may cost to send an HTLC to the target end destination.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendToRoute(self, request, context):
        """
        Deprecated, use SendToRouteV2. SendToRoute attempts to make a payment via
        the specified route. This method differs from SendPayment in that it
        allows users to specify a full route manually. This can be used for
        things like rebalancing, and atomic swaps. It differs from the newer
        SendToRouteV2 in that it doesn't return the full HTLC information.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendToRouteV2(self, request, context):
        """
        SendToRouteV2 attempts to make a payment via the specified route. This
        method differs from SendPayment in that it allows users to specify a full
        route manually. This can be used for things like rebalancing, and atomic
        swaps.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ResetMissionControl(self, request, context):
        """lncli: `resetmc`
        ResetMissionControl clears all mission control state and starts with a clean
        slate.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueryMissionControl(self, request, context):
        """lncli: `querymc`
        QueryMissionControl exposes the internal mission control state to callers.
        It is a development feature.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def XImportMissionControl(self, request, context):
        """lncli: `importmc`
        XImportMissionControl is an experimental API that imports the state provided
        to the internal mission control's state, using all results which are more
        recent than our existing values. These values will only be imported
        in-memory, and will not be persisted across restarts.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetMissionControlConfig(self, request, context):
        """lncli: `getmccfg`
        GetMissionControlConfig returns mission control's current config.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SetMissionControlConfig(self, request, context):
        """lncli: `setmccfg`
        SetMissionControlConfig will set mission control's config, if the config
        provided is valid.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QueryProbability(self, request, context):
        """lncli: `queryprob`
        Deprecated. QueryProbability returns the current success probability
        estimate for a given node pair and amount. The call returns a zero success
        probability if no channel is available or if the amount violates min/max
        HTLC constraints.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def BuildRoute(self, request, context):
        """lncli: `buildroute`
        BuildRoute builds a fully specified route based on a list of hop public
        keys. It retrieves the relevant channel policies from the graph in order to
        calculate the correct fees and time locks.
        Note that LND will use its default final_cltv_delta if no value is supplied.
        Make sure to add the correct final_cltv_delta depending on the invoice
        restriction. Moreover the caller has to make sure to provide the
        payment_addr if the route is paying an invoice which signaled it.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SubscribeHtlcEvents(self, request, context):
        """
        SubscribeHtlcEvents creates a uni-directional stream from the server to
        the client which delivers a stream of htlc events.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendPayment(self, request, context):
        """
        Deprecated, use SendPaymentV2. SendPayment attempts to route a payment
        described by the passed PaymentRequest to the final destination. The call
        returns a stream of payment status updates.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def TrackPayment(self, request, context):
        """
        Deprecated, use TrackPaymentV2. TrackPayment returns an update stream for
        the payment identified by the payment hash.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def HtlcInterceptor(self, request_iterator, context):
        """*
        HtlcInterceptor dispatches a bi-directional streaming RPC in which
        Forwarded HTLC requests are sent to the client and the client responds with
        a boolean that tells LND if this htlc should be intercepted.
        In case of interception, the htlc can be either settled, cancelled or
        resumed later by using the ResolveHoldForward endpoint.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def UpdateChanStatus(self, request, context):
        """lncli: `updatechanstatus`
        UpdateChanStatus attempts to manually set the state of a channel
        (enabled, disabled, or auto). A manual "disable" request will cause the
        channel to stay disabled until a subsequent manual request of either
        "enable" or "auto".
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_RouterServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SendPaymentV2': grpc.unary_stream_rpc_method_handler(
                    servicer.SendPaymentV2,
                    request_deserializer=router__pb2.SendPaymentRequest.FromString,
                    response_serializer=lightning__pb2.Payment.SerializeToString,
            ),
            'TrackPaymentV2': grpc.unary_stream_rpc_method_handler(
                    servicer.TrackPaymentV2,
                    request_deserializer=router__pb2.TrackPaymentRequest.FromString,
                    response_serializer=lightning__pb2.Payment.SerializeToString,
            ),
            'TrackPayments': grpc.unary_stream_rpc_method_handler(
                    servicer.TrackPayments,
                    request_deserializer=router__pb2.TrackPaymentsRequest.FromString,
                    response_serializer=lightning__pb2.Payment.SerializeToString,
            ),
            'EstimateRouteFee': grpc.unary_unary_rpc_method_handler(
                    servicer.EstimateRouteFee,
                    request_deserializer=router__pb2.RouteFeeRequest.FromString,
                    response_serializer=router__pb2.RouteFeeResponse.SerializeToString,
            ),
            'SendToRoute': grpc.unary_unary_rpc_method_handler(
                    servicer.SendToRoute,
                    request_deserializer=router__pb2.SendToRouteRequest.FromString,
                    response_serializer=router__pb2.SendToRouteResponse.SerializeToString,
            ),
            'SendToRouteV2': grpc.unary_unary_rpc_method_handler(
                    servicer.SendToRouteV2,
                    request_deserializer=router__pb2.SendToRouteRequest.FromString,
                    response_serializer=lightning__pb2.HTLCAttempt.SerializeToString,
            ),
            'ResetMissionControl': grpc.unary_unary_rpc_method_handler(
                    servicer.ResetMissionControl,
                    request_deserializer=router__pb2.ResetMissionControlRequest.FromString,
                    response_serializer=router__pb2.ResetMissionControlResponse.SerializeToString,
            ),
            'QueryMissionControl': grpc.unary_unary_rpc_method_handler(
                    servicer.QueryMissionControl,
                    request_deserializer=router__pb2.QueryMissionControlRequest.FromString,
                    response_serializer=router__pb2.QueryMissionControlResponse.SerializeToString,
            ),
            'XImportMissionControl': grpc.unary_unary_rpc_method_handler(
                    servicer.XImportMissionControl,
                    request_deserializer=router__pb2.XImportMissionControlRequest.FromString,
                    response_serializer=router__pb2.XImportMissionControlResponse.SerializeToString,
            ),
            'GetMissionControlConfig': grpc.unary_unary_rpc_method_handler(
                    servicer.GetMissionControlConfig,
                    request_deserializer=router__pb2.GetMissionControlConfigRequest.FromString,
                    response_serializer=router__pb2.GetMissionControlConfigResponse.SerializeToString,
            ),
            'SetMissionControlConfig': grpc.unary_unary_rpc_method_handler(
                    servicer.SetMissionControlConfig,
                    request_deserializer=router__pb2.SetMissionControlConfigRequest.FromString,
                    response_serializer=router__pb2.SetMissionControlConfigResponse.SerializeToString,
            ),
            'QueryProbability': grpc.unary_unary_rpc_method_handler(
                    servicer.QueryProbability,
                    request_deserializer=router__pb2.QueryProbabilityRequest.FromString,
                    response_serializer=router__pb2.QueryProbabilityResponse.SerializeToString,
            ),
            'BuildRoute': grpc.unary_unary_rpc_method_handler(
                    servicer.BuildRoute,
                    request_deserializer=router__pb2.BuildRouteRequest.FromString,
                    response_serializer=router__pb2.BuildRouteResponse.SerializeToString,
            ),
            'SubscribeHtlcEvents': grpc.unary_stream_rpc_method_handler(
                    servicer.SubscribeHtlcEvents,
                    request_deserializer=router__pb2.SubscribeHtlcEventsRequest.FromString,
                    response_serializer=router__pb2.HtlcEvent.SerializeToString,
            ),
            'SendPayment': grpc.unary_stream_rpc_method_handler(
                    servicer.SendPayment,
                    request_deserializer=router__pb2.SendPaymentRequest.FromString,
                    response_serializer=router__pb2.PaymentStatus.SerializeToString,
            ),
            'TrackPayment': grpc.unary_stream_rpc_method_handler(
                    servicer.TrackPayment,
                    request_deserializer=router__pb2.TrackPaymentRequest.FromString,
                    response_serializer=router__pb2.PaymentStatus.SerializeToString,
            ),
            'HtlcInterceptor': grpc.stream_stream_rpc_method_handler(
                    servicer.HtlcInterceptor,
                    request_deserializer=router__pb2.ForwardHtlcInterceptResponse.FromString,
                    response_serializer=router__pb2.ForwardHtlcInterceptRequest.SerializeToString,
            ),
            'UpdateChanStatus': grpc.unary_unary_rpc_method_handler(
                    servicer.UpdateChanStatus,
                    request_deserializer=router__pb2.UpdateChanStatusRequest.FromString,
                    response_serializer=router__pb2.UpdateChanStatusResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'routerrpc.Router', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Router(object):
    """
    Comments in this file will be directly parsed into the API
    Documentation as descriptions of the associated method, message, or field.
    These descriptions should go right above the definition of the object, and
    can be in either block or // comment format.

    An RPC method can be matched to an lncli command by placing a line in the
    beginning of the description in exactly the following format:
    lncli: `methodname`

    Failure to specify the exact name of the command will cause documentation
    generation to fail.

    More information on how exactly the gRPC documentation is generated from
    this proto file can be found here:
    https://github.com/lightninglabs/lightning-api

    Router is a service that offers advanced interaction with the router
    subsystem of the daemon.
    """

    @staticmethod
    def SendPaymentV2(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/routerrpc.Router/SendPaymentV2',
            router__pb2.SendPaymentRequest.SerializeToString,
            lightning__pb2.Payment.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def TrackPaymentV2(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/routerrpc.Router/TrackPaymentV2',
            router__pb2.TrackPaymentRequest.SerializeToString,
            lightning__pb2.Payment.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def TrackPayments(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/routerrpc.Router/TrackPayments',
            router__pb2.TrackPaymentsRequest.SerializeToString,
            lightning__pb2.Payment.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def EstimateRouteFee(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/EstimateRouteFee',
            router__pb2.RouteFeeRequest.SerializeToString,
            router__pb2.RouteFeeResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SendToRoute(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/SendToRoute',
            router__pb2.SendToRouteRequest.SerializeToString,
            router__pb2.SendToRouteResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SendToRouteV2(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/SendToRouteV2',
            router__pb2.SendToRouteRequest.SerializeToString,
            lightning__pb2.HTLCAttempt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ResetMissionControl(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/ResetMissionControl',
            router__pb2.ResetMissionControlRequest.SerializeToString,
            router__pb2.ResetMissionControlResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueryMissionControl(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/QueryMissionControl',
            router__pb2.QueryMissionControlRequest.SerializeToString,
            router__pb2.QueryMissionControlResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def XImportMissionControl(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/XImportMissionControl',
            router__pb2.XImportMissionControlRequest.SerializeToString,
            router__pb2.XImportMissionControlResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetMissionControlConfig(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/GetMissionControlConfig',
            router__pb2.GetMissionControlConfigRequest.SerializeToString,
            router__pb2.GetMissionControlConfigResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SetMissionControlConfig(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/SetMissionControlConfig',
            router__pb2.SetMissionControlConfigRequest.SerializeToString,
            router__pb2.SetMissionControlConfigResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def QueryProbability(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/QueryProbability',
            router__pb2.QueryProbabilityRequest.SerializeToString,
            router__pb2.QueryProbabilityResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def BuildRoute(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/BuildRoute',
            router__pb2.BuildRouteRequest.SerializeToString,
            router__pb2.BuildRouteResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SubscribeHtlcEvents(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/routerrpc.Router/SubscribeHtlcEvents',
            router__pb2.SubscribeHtlcEventsRequest.SerializeToString,
            router__pb2.HtlcEvent.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SendPayment(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/routerrpc.Router/SendPayment',
            router__pb2.SendPaymentRequest.SerializeToString,
            router__pb2.PaymentStatus.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def TrackPayment(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/routerrpc.Router/TrackPayment',
            router__pb2.TrackPaymentRequest.SerializeToString,
            router__pb2.PaymentStatus.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def HtlcInterceptor(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_stream(
            request_iterator,
            target,
            '/routerrpc.Router/HtlcInterceptor',
            router__pb2.ForwardHtlcInterceptResponse.SerializeToString,
            router__pb2.ForwardHtlcInterceptRequest.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def UpdateChanStatus(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/routerrpc.Router/UpdateChanStatus',
            router__pb2.UpdateChanStatusRequest.SerializeToString,
            router__pb2.UpdateChanStatusResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
