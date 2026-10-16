from rest_framework import serializers

from apps.equipment.models import Equipment, EquipmentStatus
from apps.equipment.serializers import EquipmentSerializer

from .models import BorrowRequest


class BorrowRequestSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        source="equipment",
        queryset=Equipment.objects.all(),
        write_only=True,
    )

    borrower = serializers.PrimaryKeyRelatedField(read_only=True)
    decided_by = serializers.PrimaryKeyRelatedField(read_only=True)
    purpose = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = BorrowRequest
        fields = [
            "id",
            "borrower",
            "equipment",
            "equipment_id",
            "pickup_date",
            "due_date",
            "purpose",
            "status",
            "decision_reason",
            "decided_by",
            "decided_at",
        ]
        read_only_fields = [
            "id",
            "borrower",
            "status",
            "decision_reason",
            "decided_by",
            "decided_at",
        ]

    def validate(self, attrs):
        """US4-4"""
        # Ensure edits are only allowed when the request is in PENDING state
        if self.instance and self.instance.status != BorrowRequest.StatusChoices.PENDING:
            raise serializers.ValidationError(
                {"non_field_errors": "Only pending borrow requests can be edited."}
            )

        if self.instance:
            pickup_date = attrs.get("pickup_date", self.instance.pickup_date)
            due_date = attrs.get("due_date", self.instance.due_date)
        else:
            pickup_date = attrs.get("pickup_date")
            due_date = attrs.get("due_date")
        equipment = attrs.get("equipment")

        if equipment:
            if getattr(equipment, "status", None) not in [
                EquipmentStatus.AVAILABLE,
            ]:
                raise serializers.ValidationError(
                    {"equipment_id": "This equipment is currently not available for borrowing."}
                )

        if attrs.get("pickup_date") or attrs.get("due_date"):
            if pickup_date > due_date:
                raise serializers.ValidationError({"due_date": "due_date must be on or after pickup_date."})

        return attrs
