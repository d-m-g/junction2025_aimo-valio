package org.example.repositories

import org.example.dto.WarehouseItem
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface WarehouseItemRepository : JpaRepository<WarehouseItem, Int>