from datetime import datetime

import stockx


def test_order_from_json() -> None:
    json_data = {
        'askId': '13658831621304650018',
        'orderNumber': '68322683-68222442',
        'listingId': '35d76ac8-a112-4d75-b44f-c8ef04a87c93',
        'amount': '140',
        'currencyCode': 'USD',
        'createdAt': '2021-08-25T13:51:47.000Z',
        'updatedAt': '2021-08-25T13:51:47.000Z',
        'variant': {
            'variantId': 'string',
            'variantName': 'Auston-Matthews-2016-Upper-Deck-Series-1-Young-Guns-Rookie-201:0',
            'variantValue': 'PSA 10'
        },
        'product': {
            'productId': 'bf364c53-eb77-4522-955c-6a6ce952cc6f',
            'productName': 'Gucci Duchessa Boston Bag',
            'styleId': 'string'
        },
        'status': 'CREATED',
        'shipment': {
            'shipByDate': 'string',
            'trackingNumber': '1Z3983AF9121770825',
            'trackingUrl': 'http://wwwapps.ups.com/etracking/tracking.cgi?tracknum=1Z3983AF9121770825',
            'carrierCode': 'UPS',
            'shippingLabelUrl': 'https://stockx.com/shipping_label.png',
            'shippingDocumentUrl': 'https://api.stockx.io/v1/selling/orders/12342334/shipping-document/S-123'
        },
        'initiatedShipments': {
            'inbound': {
                'displayId': 'string'
            }
        },
        'inventoryType': 'STANDARD',
        'authenticationDetails': {
            'status': 'string',
            'failureNotes': 'string'
        },
        'payout': {
            'totalPayout': 76.81,
            'salePrice': 79,
            'totalAdjustments': -7,
            'currencyCode': 'string',
            'adjustments': [
                {
                    'adjustmentType': 'Shipping Fee (10%)',
                    'amount': 2.13,
                    'percentage': 0.1
                }
            ]
        }
    }

    order = stockx.OrderDetail.from_json(json_data)

    # Test attributes
    assert order.number == '68322683-68222442'
    assert order.amount == 140
    assert order.status == stockx.OrderStatusActive.CREATED
    assert order.currency_code == stockx.Currency.USD

    # Test type conversions
    assert isinstance(order.created_at, datetime)
    assert order.created_at.year == 2021
    assert isinstance(order.payout, stockx.Payout)
    assert order.payout.adjustments[0].amount == 2.13


def test_batch_create_input_to_json() -> None:
    input = stockx.BatchCreateInput(
        variant_id='bf364c53-eb77-4522-955c-6a6ce952cc6f',
        amount=100,
        quantity=3,
        expires_at=datetime(2029, 6, 9),
        currency_code=stockx.Currency.AUD,
        active=True
    )
    assert input.to_json() == {
        'variantId': 'bf364c53-eb77-4522-955c-6a6ce952cc6f',
        'quantity': 3,
        'amount': '100',
        'expiresAt': '2029-06-09T00:00:00.000Z',
        'currencyCode': 'AUD',
        'active': True,
    }


def test_batch_update_input_to_json() -> None:
    input = stockx.BatchUpdateInput(
        listing_id='35d76ac8-a112-4d75-b44f-c8ef04a87c9f',
        amount=100,
        currency_code=stockx.Currency.EUR,
        expires_at=datetime(2029, 6, 9),
        active=False,
    )
    assert input.to_json() == {
        'listingId': '35d76ac8-a112-4d75-b44f-c8ef04a87c9f',
        'amount': '100',
        'currencyCode': 'EUR',
        'expiresAt': '2029-06-09T00:00:00.000Z',
        'active': False,
    }

