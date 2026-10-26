import 'package:flutter/material.dart';

import '../models/product_item.dart';
import '../models/product_notification_target.dart';
import '../services/seller_application_service.dart';
import '../services/push_notification_service.dart';
import '../session/session_service.dart';
import '../routes/app_routes.dart';
import 'product_details_screen.dart';

/// Resolves a notification ID through the existing authenticated own-products API.
class NotificationProductPage extends StatefulWidget {
  const NotificationProductPage({
    super.key,
    required this.target,
    this.service = const SellerApplicationService(),
  });
  final ProductNotificationTarget target;
  final SellerApplicationService service;
  @override
  State<NotificationProductPage> createState() =>
      _NotificationProductPageState();
}

class _NotificationProductPageState extends State<NotificationProductPage> {
  ProductItem? _product;
  String? _error;
  String _status = '', _reason = '';
  bool _signIn = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _error = null;
      _signIn = false;
    });
    try {
      final user = await SessionService.loadUser();
      final token = await SessionService.loadChatToken();
      if (user == null || token == null || token.isEmpty) {
        throw const SellerApplicationException(
          'Sign in to view this product.',
          statusCode: 401,
        );
      }
      if (user.id != widget.target.recipientId) {
        throw const SellerApplicationException(
          'This notification belongs to another account.',
        );
      }
      // The server returns only products owned by the verified bearer identity,
      // including rejected listings which cannot use the public catalog endpoint.
      final products = await widget.service.products();
      final currentUser = await SessionService.loadUser();
      final currentToken = await SessionService.loadChatToken();
      if (currentUser?.id != user.id || currentToken != token) {
        throw const SellerApplicationException(
          'Your session changed. Sign in to view this product.',
          statusCode: 401,
        );
      }
      final row = products
          .where((p) => '${p['id']}' == '${widget.target.productId}')
          .firstOrNull;
      if (row == null || row['is_archived'] == true) {
        throw const SellerApplicationException(
          'This product is no longer available.',
        );
      }
      if (!mounted) return;
      setState(() {
        _product = ProductItem.fromJson(row);
        _status = '${row['approval_status'] ?? ''}';
        _reason = '${row['rejection_reason'] ?? ''}';
      });
    } on SellerApplicationException catch (error) {
      if (mounted) {
        setState(() {
          _error = error.message;
          _signIn = error.statusCode == 401;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(
          () => _error =
              'Unable to load this product. Check your connection and retry.',
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final product = _product;
    if (product != null) {
      return ProductDetailsScreen(
        id: product.id,
        userId: widget.target.recipientId,
        sellerId: product.sellerId,
        sellerRef: product.sellerRef,
        name: product.name,
        priceLabel: product.price,
        imageUrl: product.imageUrl,
        images: product.images,
        category: product.category,
        seller: product.seller,
        sellerPhotoUrl: product.sellerPhotoUrl,
        sellerContact: product.sellerContact,
        stock: product.stock,
        description: product.description,
        expiryDate: product.expiryDate,
        inventoryStatus: product.inventoryStatus,
        inventoryStatusLabel: product.inventoryStatusLabel,
        isPurchasable: false,
        soldCount: product.soldCount,
        rating: product.rating,
        reviewsCount: product.reviewsCount,
        submittedAt: product.submittedAt,
        customization: product.customization,
        ownerView: true,
        approvalStatus: _status,
        rejectionReason: _reason,
      );
    }
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('Product Details'),
        backgroundColor: Colors.white,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: _error == null
              ? const CircularProgressIndicator()
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(_error!, textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: _signIn
                          ? () {
                              PushNotificationService.instance
                                  .deferProductNotification(widget.target);
                              Navigator.of(context).pushNamedAndRemoveUntil(
                                AppRoutes.login,
                                (_) => false,
                              );
                            }
                          : _load,
                      child: Text(_signIn ? 'Sign in' : 'Retry'),
                    ),
                  ],
                ),
        ),
      ),
    );
  }
}
