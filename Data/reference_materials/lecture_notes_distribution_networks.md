# Lecture Notes: Distribution Network Design and Strategy

## 1. Network Responsiveness vs. Cost Trade-offs
Distribution network design is the foundational architecture of any supply chain. It directly dictates both the customer service level and the total cost incurred to meet that service level.

Key dimensions of **responsiveness** include:
- **Response time**: The duration between customer order placement and receipt of goods.
- **Product variety & availability**: The breadth of catalog readily stockable and fill rates achieved.
- **Customer experience & convenience**: Order visibility, tracking accuracy, and ease of returns.
- **Order visibility**: Real-time status tracking throughout the fulfillment lifecycle.

Achieving higher responsiveness requires strategic resource commitments:
1. **Facility Costs**: Establishing facilities closer to the customer increases fixed overhead, rent, and local labor costs.
2. **Inventory Costs**: Dividing inventory across multiple local or regional facilities increases aggregate safety stock due to loss of inventory pooling benefits.
3. **Transportation Costs**: Inbound transportation costs rise because inbound freight moves in smaller, less economical lot sizes, though outbound local delivery distances and transit times decrease.

## 2. Facility Location Dynamics and Warehouse Scaling
As the number of warehouses in a distribution network increases:
- **Response time decreases**: Warehouses are located in closer geographic proximity to regional customer clusters.
- **Inventory cost increases**: Driven by the Square Root Law of Inventory, having multiple holding points multiplies buffer stock.
- **Facility overhead increases**: Each facility incurs distinct managerial, operational, and fixed maintenance expenses.
- **Transportation cost follows a convex curve**: Initially, adding warehouses decreases inbound + outbound total transportation costs by replacing long-haul Less-Than-Truckload (LTL) with Full-Truckload (FTL) bulk shipments to hubs. However, beyond an optimal point, inbound replenishment becomes highly fragmented, driving total transportation costs up again.

## 3. Real-World Industry Benchmarks
- **E-Commerce Giants (e.g., Amazon)**: Deploy tiered fulfillment models utilizing large centralized sortation hubs combined with local delivery stations to balance massive SKU variety with same-day and next-day delivery promises.
- **Direct-to-Consumer / Build-to-Order (e.g., Dell)**: Historically utilized centralized manufacturing and distribution hubs to aggregate demand variability, minimizing obsolescence and holding costs at the expense of longer delivery lead times.
