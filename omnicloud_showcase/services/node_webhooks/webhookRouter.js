const express = require('express');
const router = express.Router();

router.post('/webhooks/stripe', (req, res) => {
    const event = req.body;
    if (event.type === 'payment_intent.succeeded') {
        console.log('Payment succeeded:', event.data.object.id);
    }
    res.json({ received: true });
});

router.get('/webhooks/status', (req, res) => {
    res.json({ service: 'Webhook Consumer', status: 'online' });
});

module.exports = router;
